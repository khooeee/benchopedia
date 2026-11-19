"""Import the XCOPA test sets: 500 questions in each of eleven languages.

Run from the repository root: python3 data/xcopa/import.py
Only Python's standard library is required. The files are fetched from the
XCOPA repository at the commit pinned in benchmark.json, so a rerun reproduces
the same snapshot.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "cambridgeltl/xcopa"
LANGUAGES = ("et", "ht", "id", "it", "qu", "sw", "ta", "th", "tr", "vi", "zh")
PER_LANGUAGE = 500
FIELDS = ["changed", "choice1", "choice2", "idx", "label", "premise", "question"]
# The questions COPA's readable question file asks for each direction, as in data/copa.
QUESTIONS = {"cause": "What was the CAUSE of this?",
             "effect": "What happened as a RESULT?"}


def fetch_records(revision, language):
    path = f"data/{language}/test.{language}.jsonl"
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{path}"
    print(f"Reading {url}")
    with urllib.request.urlopen(url, timeout=120) as response:
        text = response.read().decode("utf-8")
    # The files use Windows line endings; split on those only, since other
    # line separators could occur inside text.
    if not text.endswith("\r\n") or "\n" in text.replace("\r\n", ""):
        sys.exit(f"{path}: expected CRLF-terminated lines.")
    return path, [json.loads(line) for line in text[:-2].split("\r\n")]


def to_task(record, number, path, language, revision):
    where = f"{path} line {number}"
    if sorted(record) != FIELDS:
        sys.exit(f"{where}: unexpected fields {sorted(record)}.")
    if record["idx"] != number - 1:
        sys.exit(f"{where}: idx {record['idx']} is out of order.")
    if record["question"] not in QUESTIONS or record["label"] not in (0, 1):
        sys.exit(f"{where}: unexpected question {record['question']!r} or label {record['label']!r}.")
    if not isinstance(record["changed"], bool):
        sys.exit(f"{where}: changed must be true or false.")
    for field in ("premise", "choice1", "choice2"):
        text = record[field]
        if not isinstance(text, str) or not text.strip() or text != text.strip() or "\n" in text:
            sys.exit(f"{where}: empty, padded or multi-line {field}.")
    choices = (record["choice1"], record["choice2"])
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{path}#L{number}"
    return {
        "key": f"{language}-{record['idx']}",
        "prompt": (f"Premise: {record['premise']} {QUESTIONS[record['question']]}\n\n"
                   f"Alternative 1: {choices[0]}\n\nAlternative 2: {choices[1]}"),
        "solution": f"Alternative {record['label'] + 1}: {choices[record['label']]}",
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be a full Git commit SHA.")
    expected = PER_LANGUAGE * len(LANGUAGES)
    if benchmark["task_count"] != expected:
        sys.exit(f"The declared scope must be all {expected:,} test questions.")
    tasks = []
    for language in LANGUAGES:
        path, records = fetch_records(revision, language)
        if len(records) != PER_LANGUAGE:
            sys.exit(f"{path}: expected {PER_LANGUAGE} questions, found {len(records)}.")
        labels = [record["label"] for record in records]
        if labels.count(0) != labels.count(1):
            sys.exit(f"{path}: answer positions are not balanced.")
        tasks.extend(to_task(record, number, path, language, revision)
                     for number, record in enumerate(records, start=1))
    # Every language translates the same 500 COPA questions, which share their answers.
    answers = {}
    for task in tasks:
        language, number = task["key"].split("-")
        answers.setdefault(number, set()).add(task["solution"].split(":")[0])
    if any(len(positions) != 1 for positions in answers.values()):
        sys.exit("Languages disagree on the answer to a question.")
    if len({task["key"] for task in tasks}) != expected:
        sys.exit("Keys are not unique.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} XCOPA test questions to {out}")


if __name__ == "__main__":
    main()
