"""Import all 4,326 SimpleQA questions from OpenAI's published test file.

Run from the repository root: python3 data/simpleqa/import.py
Only Python's standard library is required.
"""

import csv
import hashlib
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
SOURCE_URL = "https://openaipublic.blob.core.windows.net/simple-evals/simple_qa_test_set.csv"
COLUMNS = ["metadata", "problem", "answer"]
EXPECTED_COUNT = 4326


def fetch_rows(checksum):
    # The file is not versioned, so the pinned SHA-256 stands in for a revision.
    with urllib.request.urlopen(SOURCE_URL, timeout=120) as response:
        payload = response.read()
    if hashlib.sha256(payload).hexdigest() != checksum:
        raise ValueError("The published file differs from the pinned SHA-256.")
    reader = csv.DictReader(io.StringIO(payload.decode("utf-8"), newline=""))
    if reader.fieldnames != COLUMNS:
        raise ValueError(f"Unexpected columns: {reader.fieldnames}")
    return list(reader)


def to_task(number, row):
    where = f"Row {number}"
    problem, answer = row["problem"], row["answer"]
    if not problem.strip() or not answer.strip():
        raise ValueError(f"{where}: missing problem or answer")
    return {
        "key": f"test-{number:04d}",
        "prompt": problem,
        "solution": answer,
        "prompt_source_url": SOURCE_URL,
        "solution_source_url": SOURCE_URL,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    checksum = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{64}", checksum):
        sys.exit("dataset_revision must be the SHA-256 of the published test file.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 4,326 SimpleQA questions.")
    rows = fetch_rows(checksum)
    tasks = [to_task(number, row) for number, row in enumerate(rows, start=1)]
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("SimpleQA count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} SimpleQA questions to {out}")


if __name__ == "__main__":
    main()
