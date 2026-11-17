"""Import the 19,998 labelled FEVER shared-task development claims.

Run from the repository root: python3 data/fever/import.py
Only Python's standard library is required. The importer also rewrites
ATTRIBUTION.md, which credits every Wikipedia article the evidence comes from.
It reads the authors' pre-processed Wikipedia archive, 1.7 GB, to recover the
cited sentences, and keeps only those: nothing else of that archive is stored.
"""

import hashlib
import json
import re
import sys
import tempfile
import unicodedata
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
SPLIT_URL = "https://fever.ai/download/fever/shared_task_dev.jsonl"
WIKI_URL = "https://fever.ai/download/fever/wiki-pages.zip"
WIKI_SHA256 = "4b06d95da6adf7fe02d2796176c670dacccb21348da89cba4c50676ab99665f2"
WIKI_MEMBER = re.compile(r"wiki-pages/wiki-\d+\.jsonl")
EXPECTED_COUNT = 19998
EXPECTED_LABELS = {"SUPPORTS": 6666, "REFUTES": 6666, "NOT ENOUGH INFO": 6666}
EXPECTED_PAGES = 2892
EXPECTED_SENTENCES = 7100
RECORD_FIELDS = ["claim", "evidence", "id", "label", "verifiable"]
# Spaces and brackets as the authors' Wikipedia processing writes them.
TITLE_ESCAPES = {"_": " ", "-LRB-": "(", "-RRB-": ")", "-COLON-": ":"}


def download(url, checksum, path):
    """Stream one published file to disk and check it is the revision under review."""
    digest = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=1200) as response, path.open("wb") as out:
        while chunk := response.read(1 << 20):
            digest.update(chunk)
            out.write(chunk)
    if digest.hexdigest() != checksum:
        sys.exit(f"{url} has digest {digest.hexdigest()}, not the reviewed {checksum}.")


def fetch(url, checksum):
    with urllib.request.urlopen(url, timeout=600) as response:
        payload = response.read()
    if hashlib.sha256(payload).hexdigest() != checksum:
        sys.exit(f"{url} is not the revision under review.")
    return payload.decode("utf-8")


def claims(text):
    """Yield each claim of the split, after checking its shape."""
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        record = json.loads(line)
        if sorted(record) != RECORD_FIELDS:
            sys.exit(f"line {number}: expected the fields {RECORD_FIELDS}.")
        if record["label"] not in EXPECTED_LABELS:
            sys.exit(f"line {number}: unexpected label {record['label']!r}.")
        if not isinstance(record["id"], int) or record["id"] < 0:
            sys.exit(f"line {number}: unexpected claim identifier.")
        if not record["claim"].strip() or "\n" in record["claim"]:
            sys.exit(f"line {number}: empty or multi-line claim.")
        verifiable = "NOT VERIFIABLE" if record["label"] == "NOT ENOUGH INFO" else "VERIFIABLE"
        if record["verifiable"] != verifiable:
            sys.exit(f"line {number}: label and verifiable field disagree.")
        yield record


def evidence_sets(record):
    """Return the distinct evidence sets of one claim, in the order first recorded."""
    found = []
    for group in record["evidence"]:
        cited = []
        for entry in group:
            if len(entry) != 4:
                sys.exit(f"claim {record['id']}: unexpected evidence tuple.")
            _, _, page, sentence = entry
            if page is None or sentence is None:
                if page is not None or sentence is not None:
                    sys.exit(f"claim {record['id']}: half-empty evidence tuple.")
                continue
            if not isinstance(page, str) or not page.strip():
                sys.exit(f"claim {record['id']}: unexpected evidence page.")
            if not isinstance(sentence, int) or sentence < 0:
                sys.exit(f"claim {record['id']}: unexpected sentence number.")
            cited.append((page, sentence))
        if cited:
            found.append(tuple(cited))
    distinct = list(dict.fromkeys(found))
    if (record["label"] == "NOT ENOUGH INFO") == bool(distinct):
        sys.exit(f"claim {record['id']}: evidence does not match the label.")
    return distinct


def sentences_of(lines):
    """Split one page's stored lines into sentence number to sentence."""
    found = {}
    for row in lines.split("\n"):
        if not row:
            continue
        parts = row.split("\t")
        if not re.fullmatch(r"\d+", parts[0]):
            raise ValueError(f"unexpected stored line {row[:40]!r}")
        found[int(parts[0])] = parts[1] if len(parts) > 1 else ""
    return found


def wikipedia(archive_path, wanted):
    """Return the cited sentences, read from the authors' processed Wikipedia.

    The claims file and the archive disagree on the Unicode normalisation of 32
    page titles, so pages are matched by their normalised titles.
    """
    index = {unicodedata.normalize("NFC", page): page for page in wanted}
    found = {}
    with zipfile.ZipFile(archive_path) as archive:
        members = sorted(name for name in archive.namelist() if WIKI_MEMBER.fullmatch(name))
        if not members:
            sys.exit(f"{WIKI_URL}: no page files in the archive.")
        for name in members:
            with archive.open(name) as stream:
                for line in stream:
                    if not line.strip():
                        continue
                    page = json.loads(line)
                    title = index.get(unicodedata.normalize("NFC", page["id"]))
                    if title is not None:
                        found[title] = sentences_of(page["lines"])
    missing = sorted(set(wanted) - set(found))
    if missing:
        sys.exit(f"{WIKI_URL}: no page stored for {missing[0]!r}.")
    return found


def to_task(record, sets, pages):
    lines = []
    for number, group in enumerate(sets, start=1):
        cited = []
        for page, sentence in group:
            text = pages[page].get(sentence, "")
            if not text.strip():
                sys.exit(f"claim {record['id']}: {page} has no sentence {sentence}.")
            cited.append(f"{page} (sentence {sentence}): {text}")
        lines.append(f"Evidence set {number}:\n" + "\n".join(cited))
    solution = record["label"]
    if lines:
        solution += "\n\n" + "\n".join(lines)
    return {
        "key": str(record["id"]),
        "prompt": record["claim"],
        "solution": solution,
        "prompt_source_url": SPLIT_URL,
        "solution_source_url": SPLIT_URL,
    }


def write_attribution(titles):
    lines = []
    for title in sorted(titles):
        article = title
        for escape, character in TITLE_ESCAPES.items():
            article = article.replace(escape, character)
        path = urllib.parse.quote(article.replace(" ", "_"), safe="_,()'!:.-")
        lines.append(f"- [{article}](https://en.wikipedia.org/wiki/{path})")
    text = f"""# FEVER attribution

The evidence sentences in this snapshot were written by contributors to these
{len(titles):,} English Wikipedia articles and are shared under the Creative Commons
Attribution-ShareAlike terms the upstream notice defers to, currently
[version 4.0](https://creativecommons.org/licenses/by-sa/4.0/legalcode) and
[version 3.0](https://creativecommons.org/licenses/by-sa/3.0/legalcode) for
material from before June 2023. Each line gives the article title with the
bracket and space escapes of the upstream page identifiers undone, and a link to
the article. FEVER drew its sentences from the English Wikipedia dump of June
2017 and does not record which revision each came from, so these links point at
the article as it stands now, not as the annotator read it.

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
        sys.exit(f"The declared scope must be all {EXPECTED_COUNT} development claims.")
    records = list(claims(fetch(SPLIT_URL, revision)))
    if len(records) != EXPECTED_COUNT:
        sys.exit(f"Expected {EXPECTED_COUNT} claims, found {len(records)}.")
    labels = {label: 0 for label in EXPECTED_LABELS}
    sets = {}
    for record in records:
        labels[record["label"]] += 1
        sets[record["id"]] = evidence_sets(record)
    if labels != EXPECTED_LABELS:
        sys.exit(f"Label counts differ from the declared scope: {labels}.")
    cited = {(page, sentence) for groups in sets.values()
             for group in groups for page, sentence in group}
    titles = {page for page, _ in cited}
    if len(titles) != EXPECTED_PAGES or len(cited) != EXPECTED_SENTENCES:
        sys.exit(f"Expected {EXPECTED_SENTENCES} sentences on {EXPECTED_PAGES} pages, "
                 f"found {len(cited)} on {len(titles)}.")
    with tempfile.TemporaryDirectory() as workspace:
        archive = Path(workspace) / "wiki-pages.zip"
        print(f"Reading {WIKI_URL} for the {len(cited):,} cited sentences; this is 1.7 GB.")
        download(WIKI_URL, WIKI_SHA256, archive)
        pages = wikipedia(archive, titles)
    tasks = [to_task(record, sets[record["id"]], pages) for record in records]
    tasks.sort(key=lambda task: int(task["key"]))
    if len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("FEVER claim identifiers differ from the declared scope.")
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
    print(f"Wrote {len(tasks):,} FEVER development claims with {len(cited):,} evidence "
          f"sentences from {len(titles):,} Wikipedia articles to {out}")


if __name__ == "__main__":
    main()
