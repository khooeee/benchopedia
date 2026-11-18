"""Import the 7,405 HotpotQA distractor development questions from the pinned file.

Run from the repository root: python3 data/hotpotqa/import.py
Only Python's standard library is required. The importer also rewrites
ATTRIBUTION.md, which credits every Wikipedia article the paragraphs come from.
The authors' own download host no longer resolves, so the file is read from the
Internet Archive's copy of their download link and checked against its digest.
"""

import hashlib
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
SPLIT_URL = ("https://web.archive.org/web/20260310132809id_/"
             "http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json")
EXPECTED_COUNT = 7405
EXPECTED_ARTICLES = 66581
# The distractor setting gives ten paragraphs, but 60 questions carry fewer.
EXPECTED_TEN_PARAGRAPHS = 7345
EXPECTED_TYPES = {"bridge": 5918, "comparison": 1487}
# One supporting fact names a sentence its paragraph does not have.
EXPECTED_UNRESOLVED = 1
RECORD_FIELDS = ["_id", "answer", "context", "level", "question", "supporting_facts", "type"]


def fetch(url, checksum):
    """Read the pinned file and check it is the revision under review."""
    with urllib.request.urlopen(url, timeout=600) as response:
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != checksum:
        sys.exit(f"{url} has digest {digest}, not the reviewed {checksum}.")
    return json.loads(payload)


def paragraphs(record):
    """Return the record's paragraphs as article title to list of sentences."""
    found = {}
    for entry in record["context"]:
        if len(entry) != 2:
            raise ValueError(f"{record['_id']}: expected a title and its sentences")
        title, sentences = entry
        if not isinstance(title, str) or not title.strip() or "\n" in title:
            raise ValueError(f"{record['_id']}: empty or multi-line paragraph title")
        if re.match(r"^#{1,6}\s|^\s*[-*]\s", title):
            raise ValueError(f"{record['_id']}: paragraph title would read as markup")
        if title in found:
            raise ValueError(f"{record['_id']}: paragraph title {title!r} appears twice")
        if not sentences or not all(isinstance(line, str) for line in sentences):
            raise ValueError(f"{record['_id']}: empty paragraph")
        if any("\n" in line for line in sentences):
            raise ValueError(f"{record['_id']}: newline inside a sentence")
        found[title] = sentences
    return found


def supporting(record, found):
    """Return one line per supporting fact: its article, sentence number, sentence."""
    lines = []
    unresolved = 0
    for entry in record["supporting_facts"]:
        if len(entry) != 2:
            raise ValueError(f"{record['_id']}: expected a title and a sentence number")
        title, index = entry
        if title not in found:
            raise ValueError(f"{record['_id']}: supporting fact cites a missing paragraph")
        if not isinstance(index, int) or index < 0:
            raise ValueError(f"{record['_id']}: unexpected sentence number {index!r}")
        if index >= len(found[title]):
            # Recorded upstream against a paragraph that has no such sentence.
            unresolved += 1
            lines.append(f"{title} (sentence {index})")
        else:
            lines.append(f"{title} (sentence {index}): {found[title][index].strip()}")
    if not lines:
        raise ValueError(f"{record['_id']}: no supporting facts")
    return lines, unresolved


def to_task(record):
    if sorted(record) != RECORD_FIELDS:
        raise ValueError(f"Expected the record fields {RECORD_FIELDS}.")
    key = record["_id"]
    if not re.fullmatch(r"[0-9a-f]{24}", key):
        raise ValueError(f"{key}: unexpected question identifier")
    if record["type"] not in EXPECTED_TYPES or record["level"] != "hard":
        raise ValueError(f"{key}: unexpected question type or difficulty")
    for field in ("question", "answer"):
        if not record[field].strip() or "\n" in record[field]:
            raise ValueError(f"{key}: empty or multi-line {field}")
    found = paragraphs(record)
    lines, unresolved = supporting(record, found)
    body = "\n\n".join(f"# {title}\n\n{''.join(sentences).strip()}"
                       for title, sentences in found.items())
    return {
        "key": key,
        "prompt": f"{record['question']}\n\n{body}",
        "solution": record["answer"] + "\n\nSupporting sentences:\n" + "\n".join(lines),
        "prompt_source_url": SPLIT_URL,
        "solution_source_url": SPLIT_URL,
    }, set(found), unresolved


def write_attribution(titles):
    lines = []
    for title in sorted(titles):
        path = urllib.parse.quote(title.replace(" ", "_"), safe="_,()'!:.-")
        lines.append(f"- [{title}](https://en.wikipedia.org/wiki/{path})")
    text = f"""# HotpotQA attribution

The paragraphs in this snapshot are the opening paragraphs of these {len(titles):,}
English Wikipedia articles, written by Wikipedia contributors and shared under the
[Creative Commons Attribution-ShareAlike 4.0 International license](https://creativecommons.org/licenses/by-sa/4.0/legalcode).
Each line gives the article title as the upstream file records it and a link to
the article. HotpotQA built its paragraphs from the English Wikipedia dump of
1 October 2017 and does not record which revision each paragraph came from, so
these links point at the article as it stands now, not as the question's writer
read it.

This file is generated by import.py from the pinned development split.

"""
    (BENCHMARK_DIR / "ATTRIBUTION.md").write_text(text + "\n".join(lines) + "\n",
                                                  encoding="utf-8")


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{64}", revision):
        sys.exit("dataset_revision must be the SHA-256 digest of the split file.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit(f"The declared scope must be all {EXPECTED_COUNT} development questions.")
    records = fetch(SPLIT_URL, revision)
    if not isinstance(records, list) or len(records) != EXPECTED_COUNT:
        sys.exit(f"Expected {EXPECTED_COUNT} questions in the split file.")
    tasks, titles, unresolved, ten = [], set(), 0, 0
    kinds = {kind: 0 for kind in EXPECTED_TYPES}
    for record in records:
        task, found, missing = to_task(record)
        tasks.append(task)
        titles |= found
        unresolved += missing
        ten += len(found) == 10
        kinds[record["type"]] += 1
    if ten != EXPECTED_TEN_PARAGRAPHS:
        sys.exit(f"Expected {EXPECTED_TEN_PARAGRAPHS} questions with ten paragraphs, "
                 f"found {ten}.")
    if kinds != EXPECTED_TYPES:
        sys.exit(f"Question types differ from the declared scope: {kinds}.")
    if len(titles) != EXPECTED_ARTICLES:
        sys.exit(f"Expected {EXPECTED_ARTICLES} articles, found {len(titles)}.")
    if unresolved != EXPECTED_UNRESOLVED:
        sys.exit(f"Expected {EXPECTED_UNRESOLVED} supporting fact(s) without a "
                 f"sentence, found {unresolved}.")
    tasks.sort(key=lambda task: task["key"])
    if len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("HotpotQA identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    write_attribution(titles)
    print(f"Wrote {len(tasks):,} HotpotQA development questions over "
          f"{len(titles):,} Wikipedia articles to {out}")


if __name__ == "__main__":
    main()
