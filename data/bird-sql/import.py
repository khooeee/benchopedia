"""Import all 1,534 BIRD-SQL development questions from their pinned Hugging Face revision.

Run from the repository root: python3 data/bird-sql/import.py
Only Python's standard library is required.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "birdsql/bird_sql_dev_20251106"
DATA_PATH = "data/dev_20251106-00000-of-00001.json"
# Development database and its expected question count.
DATABASES = {
    "california_schools": 89,
    "financial": 106,
    "toxicology": 145,
    "card_games": 191,
    "codebase_community": 186,
    "superhero": 129,
    "formula_1": 174,
    "european_football_2": 129,
    "thrombosis_prediction": 163,
    "student_club": 158,
    "debit_card_specializing": 64,
}
EXPECTED_COUNT = sum(DATABASES.values())
FIELDS = {"question_id", "db_id", "question", "evidence", "SQL", "difficulty"}
DIFFICULTIES = {"simple", "moderate", "challenging"}


def fetch_questions(revision):
    url = f"https://huggingface.co/datasets/{REPOSITORY}/resolve/{revision}/{DATA_PATH}"
    with urllib.request.urlopen(url, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def to_task(number, record, revision):
    where = f"question {number}"
    if not isinstance(record, dict) or set(record) != FIELDS:
        raise ValueError(f"{where}: unexpected fields")
    if record["question_id"] != number:
        raise ValueError(f"{where}: question IDs must run from 0 in file order")
    if record["db_id"] not in DATABASES or record["difficulty"] not in DIFFICULTIES:
        raise ValueError(f"{where}: unknown database or difficulty")
    for field in ("question", "SQL"):
        text = record[field]
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{where}: missing {field}")
    evidence = record["evidence"]
    if not isinstance(evidence, str):
        raise ValueError(f"{where}: evidence must be text")
    parts = [record["question"], f"Database: {record['db_id']}"]
    # Empty or whitespace-only evidence adds nothing to show.
    if evidence.strip():
        parts.append(f"Evidence: {evidence}")
    source = f"https://huggingface.co/datasets/{REPOSITORY}/blob/{revision}/{DATA_PATH}"
    return {
        "key": f"question-{number:04d}",
        "prompt": "\n\n".join(parts),
        "solution": record["SQL"],
        "prompt_source_url": source,
        "solution_source_url": source,
        "environment_url": f"https://huggingface.co/datasets/{REPOSITORY}/blob/{revision}/README.md",
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable Hugging Face commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 1,534 BIRD-SQL development questions.")
    records = fetch_questions(revision)
    if not isinstance(records, list) or len(records) != EXPECTED_COUNT:
        sys.exit(f"Expected {EXPECTED_COUNT} questions in {DATA_PATH}.")
    tasks = [to_task(number, record, revision) for number, record in enumerate(records)]
    for database, count in DATABASES.items():
        found = sum(record["db_id"] == database for record in records)
        if found != count:
            sys.exit(f"{database}: expected {count} questions, found {found}.")
    tasks.sort(key=lambda task: task["key"])
    if len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("BIRD-SQL identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} BIRD-SQL questions to {out}")


if __name__ == "__main__":
    main()
