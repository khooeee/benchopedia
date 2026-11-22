"""Score FEVER labels and ranked evidence with the shared task's metrics.

The local retrieval baseline searches the pinned Wikipedia index by title.
https://github.com/sheffieldnlp/fever-scorer/blob/4801615100fbf6327f8e99b5dbaefe5dd890e869/src/fever/scorer.py
"""

from contextlib import closing
from functools import lru_cache
import json
from pathlib import Path
import re
import sqlite3
import unicodedata


ATTEMPTS = 1
MAX_EVIDENCE = 5
WIKI_SHA256 = "4b06d95da6adf7fe02d2796176c670dacccb21348da89cba4c50676ab99665f2"
LABELS = {"SUPPORTS", "REFUTES", "NOT ENOUGH INFO"}
NO_EVIDENCE = "NOT ENOUGH INFO"
FACT = re.compile(r"^(.+?) \(sentence ([0-9]+)\): ")
WORDS = re.compile(r"[^\W_]+")
STOPWORDS = frozenset("the and for are was has that with from have who were been only his her its their one".split())


def index_path():
    root = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
    return root / "build" / "fever-wikipedia.sqlite"


def open_index():
    return sqlite3.connect(index_path().as_uri() + "?mode=ro&immutable=1", uri=True)


@lru_cache(maxsize=1)
def check_setup():
    try:
        with closing(open_index()) as conn:
            revision = conn.execute("SELECT wiki_sha256 FROM metadata").fetchone()
            conn.execute("SELECT term FROM title_terms LIMIT 1").fetchone()
        if revision == (WIKI_SHA256,):
            return None
    except sqlite3.Error:
        pass
    return "Run python3 data/fever/setup_eval.py to index the pinned Wikipedia snapshot"


def keywords(text):
    return [word for word in WORDS.findall(text.casefold()) if len(word) > 2 and word not in STOPWORDS]


def passage_candidates(claim):
    terms = tuple(dict.fromkeys(keywords(claim)))[:8]
    if not terms:
        return []
    indexed_terms = tuple(dict.fromkeys(
        "".join(ch for ch in unicodedata.normalize("NFKD", term) if not unicodedata.combining(ch))
        for term in terms
    ))
    placeholders = ", ".join("?" for _ in indexed_terms)
    with closing(open_index()) as conn:
        rare = conn.execute(
            f"SELECT term FROM title_terms WHERE term IN ({placeholders}) ORDER BY doc, term LIMIT 3",
            indexed_terms,
        ).fetchall()
        query = " OR ".join(f'"{term}"' for term in ([row[0] for row in rare] or terms[:2]))
        pages = conn.execute("""
            SELECT pages.id, pages.lines FROM (
                SELECT rowid FROM titles WHERE titles MATCH ? ORDER BY rank LIMIT 8
            ) hits JOIN pages ON pages.rowid = hits.rowid
        """, (query,)).fetchall()
    wanted = set(terms)
    result = []
    for page, lines in pages:
        relevant = []
        for line in lines.split("\n"):
            number, _, sentence = line.partition("\t")
            if number.isdecimal() and sentence.strip():
                match = len(wanted.intersection(keywords(sentence)))
                relevant.append((match, int(number), sentence))
        top = sorted(relevant, key=lambda row: (-row[0], row[1]))[:8]
        if top:
            text = "\n".join(f"{number}: {sentence[:500]}" for _, number, sentence in top)
            result.append(f"{page}\n{text}")
    return result


def messages(task):
    passages = "\n\n".join(passage_candidates(task["prompt"]))
    instruction = ('Verify the claim using the numbered Wikipedia evidence below. Reply as JSON with '
                   '"label" (SUPPORTS, REFUTES, or NOT ENOUGH INFO) and "evidence" '
                   '(up to five [exact page id, sentence number] pairs in relevance order).')
    return [{"role": "user", "content": f"{instruction}\n\nClaim: {task['prompt']}\n\n{passages}"}]


def references(task):
    label, _, evidence = task["solution"].partition("\n\n")
    groups = []
    for line in evidence.split("\n") if evidence else ():
        if line.startswith("Evidence set "):
            groups.append([])
        else:
            match = FACT.match(line)
            if match is None or not groups:
                raise ValueError(f"{task['key']}: invalid reference evidence")
            groups[-1].append((match[1], int(match[2])))
    return label, groups


def score(task, output):
    try:
        decoded = json.loads(output)
    except json.JSONDecodeError:
        return None
    if not isinstance(decoded, dict):
        return None
    label, evidence = decoded.get("label"), decoded.get("evidence")
    if not isinstance(label, str) or label.upper() not in LABELS or not isinstance(evidence, list):
        return None
    if not all(isinstance(pair, list) and len(pair) == 2 and isinstance(pair[0], str)
               and type(pair[1]) is int for pair in evidence):
        return None
    reference_label, groups = references(task)
    correct_label = int(label.upper() == reference_label)
    metrics = {"label-accuracy": correct_label, "fever-score": correct_label}
    if reference_label != NO_EVIDENCE:
        ranked = [tuple(pair) for pair in evidence[:MAX_EVIDENCE]]
        correct_sentences = {pair for group in groups for pair in group}
        complete = int(any(all(pair in ranked for pair in group) for group in groups))
        precision = sum(pair in correct_sentences for pair in ranked) / len(ranked) if ranked else 1.0
        metrics.update({"fever-score": correct_label * complete, "evidence-precision": precision,
                        "evidence-recall": complete})
    return metrics


def reference_output(task):
    label, groups = references(task)
    evidence = min(groups, key=len) if groups else []
    return json.dumps({"label": label, "evidence": evidence}, ensure_ascii=False)
