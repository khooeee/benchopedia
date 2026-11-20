"""Import all 14,267 PopQA questions from the authors' published TSV file.

Run from the repository root: python3 data/popqa/import.py
Only Python's standard library is required. The file is fetched from the
adaptive-retrieval repository at the commit pinned in benchmark.json and checked
against its size and SHA-256 digest, so a rerun reproduces the same snapshot.
"""

import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "AlexTMallen/adaptive-retrieval"
FILE = "data/popQA.tsv"
FILE_SHA256 = "9a5227f41bff0e4c331d4a774d946b12f95307892b58f860a9606ef356e6089b"
COLUMNS = ["id", "subj", "prop", "obj", "subj_id", "prop_id", "obj_id", "s_aliases", "o_aliases",
           "s_uri", "o_uri", "s_wiki_title", "o_wiki_title", "s_pop", "o_pop", "question",
           "possible_answers"]
EXPECTED = 14267
# The question template for each of the 16 relationship types, from the
# q_templates table in the authors' run_model.py.
TEMPLATES = {
    "occupation": "What is {}'s occupation?",
    "place of birth": "In what city was {} born?",
    "genre": "What genre is {}?",
    "father": "Who is the father of {}?",
    "country": "In what country is {}?",
    "producer": "Who was the producer of {}?",
    "director": "Who was the director of {}?",
    "capital of": "What is {} the capital of?",
    "screenwriter": "Who was the screenwriter for {}?",
    "composer": "Who was the composer of {}?",
    "color": "What color is {}?",
    "religion": "What is the religion of {}?",
    "sport": "What sport does {} play?",
    "author": "Who is the author of {}?",
    "mother": "Who is the mother of {}?",
    "capital": "What is the capital of {}?",
}


def fetch_rows(revision):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{FILE}"
    print(f"Reading {url}")
    with urllib.request.urlopen(url, timeout=300) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != FILE_SHA256:
        sys.exit(f"{FILE}: SHA-256 digest does not match the pinned file.")
    reader = csv.DictReader(io.StringIO(data.decode("utf-8"), newline=""), delimiter="\t")
    if reader.fieldnames != COLUMNS:
        sys.exit(f"{FILE}: unexpected columns {reader.fieldnames}.")
    return list(reader)


def to_task(row, source):
    where = f"question {row['id']}"
    if not re.fullmatch(r"[1-9][0-9]*", row["id"]):
        sys.exit(f"{where}: unexpected id.")
    template = TEMPLATES.get(row["prop"])
    if template is None:
        sys.exit(f"{where}: unknown relationship type {row['prop']!r}.")
    question = row["question"]
    if question != template.format(row["subj"]):
        sys.exit(f"{where}: question does not follow the {row['prop']!r} template.")
    answers = json.loads(row["possible_answers"])
    if not isinstance(answers, list) or not answers:
        sys.exit(f"{where}: missing answers.")
    for answer in answers:
        if not isinstance(answer, str) or not answer.strip() or "\n" in answer:
            sys.exit(f"{where}: unexpected answer {answer!r}.")
    if row["obj"] not in answers:
        sys.exit(f"{where}: the triple's object is not among its answers.")
    # Some aliases repeat within a list; each is listed once, in published order.
    unique = list(dict.fromkeys(answers))
    return {
        "key": row["id"],
        "prompt": question,
        "solution": "\n".join(unique),
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be a full Git commit SHA.")
    if benchmark["task_count"] != EXPECTED:
        sys.exit(f"The declared scope must be all {EXPECTED:,} PopQA questions.")
    rows = fetch_rows(revision)
    if len(rows) != EXPECTED:
        sys.exit(f"{FILE}: expected {EXPECTED:,} questions, found {len(rows):,}.")
    if len({row["id"] for row in rows}) != EXPECTED:
        sys.exit(f"{FILE}: question ids are not unique.")
    types = Counter(row["prop"] for row in rows)
    if set(types) != set(TEMPLATES):
        sys.exit(f"{FILE}: unexpected relationship types {sorted(types)}.")
    # GitHub cannot display a file this large, so links point at the file.
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{FILE}"
    tasks = [to_task(row, source) for row in sorted(rows, key=lambda row: int(row["id"]))]
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} PopQA questions to {out}")


if __name__ == "__main__":
    main()
