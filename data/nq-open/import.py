"""Import the 3,610 questions of the original NQ-Open development split.

Run from the repository root: python3 data/nq-open/import.py
Only Python's standard library is required. The file is fetched from the
Natural Questions repository at the commit pinned in benchmark.json, so a
rerun reproduces the same snapshot.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "google-research-datasets/natural-questions"
PATH = "nq_open/NQ-open.dev.jsonl"
EXPECTED_COUNT = 3610
# Lee et al. kept only answers of at most five tokens. Split on spaces, one
# answer in this split, "Vice President George H. W. Bush", has six words.
MAX_ANSWER_WORDS = 6


def fetch_lines(revision):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{PATH}"
    print(f"Reading {url}")
    with urllib.request.urlopen(url, timeout=120) as response:
        text = response.read().decode("utf-8")
    if not text.endswith("\n"):
        sys.exit(f"{PATH} does not end with a newline; it may be truncated.")
    # Split on newlines only: Unicode line separators may occur inside text.
    return text[:-1].split("\n")


def to_task(line, number, revision):
    where = f"line {number}"
    record = json.loads(line)
    if sorted(record) != ["answer", "question"]:
        sys.exit(f"{where}: expected only a question and its answers, found {sorted(record)}.")
    question, answers = record["question"], record["answer"]
    if not isinstance(question, str) or not question.strip() or question != question.strip():
        sys.exit(f"{where}: empty or padded question.")
    if (not isinstance(answers, list) or not answers
            or any(not isinstance(a, str) or not a.strip() or "\n" in a for a in answers)):
        sys.exit(f"{where}: expected a list of non-empty, single-line answers.")
    if len(set(answers)) != len(answers):
        sys.exit(f"{where}: repeated answer.")
    if any(len(answer.split()) > MAX_ANSWER_WORDS for answer in answers):
        sys.exit(f"{where}: an answer is longer than NQ-Open allows.")
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{PATH}#L{number}"
    return {
        "key": f"dev-{number:04d}",
        "prompt": question,
        "solution": "\n".join(answers),
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be a full Git commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit(f"The declared scope must be all {EXPECTED_COUNT:,} questions of the original dev split.")
    lines = fetch_lines(revision)
    tasks = [to_task(line, number, revision) for number, line in enumerate(lines, start=1)]
    if len(tasks) != EXPECTED_COUNT:
        sys.exit(f"Expected {EXPECTED_COUNT:,} questions, found {len(tasks):,}.")
    # The official scorer keys references by question text, so every question must be distinct.
    if len({task["prompt"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("The split repeats a question.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} NQ-Open questions to {out}")


if __name__ == "__main__":
    main()
