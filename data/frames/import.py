"""Import all 824 FRAMES questions from their pinned Hugging Face revision.

Run from the repository root: python3 data/frames/import.py
Only Python's standard library is required.
"""

import csv
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "google/frames-benchmark"
DATA_PATH = "test.tsv"
EXPECTED_COUNT = 824
LINK_COLUMNS = [f"wikipedia_link_{number}" for number in range(1, 11)] + ["wikipedia_link_11+"]
COLUMNS = ["", "Prompt", "Answer", *LINK_COLUMNS, "reasoning_types", "wiki_links"]


def fetch_rows(revision):
    url = f"https://huggingface.co/datasets/{REPOSITORY}/resolve/{revision}/{DATA_PATH}"
    with urllib.request.urlopen(url, timeout=120) as response:
        text = response.read().decode("utf-8")
    reader = csv.reader(io.StringIO(text, newline=""), delimiter="\t", strict=True)
    if next(reader) != COLUMNS:
        raise ValueError(f"{DATA_PATH}: unexpected columns")
    rows = list(reader)
    if any(len(row) != len(COLUMNS) for row in rows):
        raise ValueError(f"{DATA_PATH}: a row has the wrong number of columns")
    return [dict(zip(COLUMNS, row)) for row in rows]


def to_task(number, row, revision):
    where = f"row {number}"
    if row[""] != str(number):
        raise ValueError(f"{where}: row indexes must run from 0 in file order")
    for field in ("Prompt", "Answer"):
        if not row[field].strip():
            raise ValueError(f"{where}: missing {field}")
    # Link cells are shown as published, including the overflow cell's comma-joined links.
    links = [row[column] for column in LINK_COLUMNS if row[column].strip()]
    if not links:
        raise ValueError(f"{where}: no Wikipedia articles listed")
    source = f"https://huggingface.co/datasets/{REPOSITORY}/blob/{revision}/{DATA_PATH}"
    return {
        "key": f"question-{number:03d}",
        "prompt": row["Prompt"],
        "solution": row["Answer"] + "\n\nWikipedia articles:\n" + "\n".join(links),
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable Hugging Face commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 824 FRAMES questions.")
    rows = fetch_rows(revision)
    if len(rows) != EXPECTED_COUNT:
        sys.exit(f"Expected {EXPECTED_COUNT} questions in {DATA_PATH}, found {len(rows)}.")
    tasks = [to_task(number, row, revision) for number, row in enumerate(rows)]
    tasks.sort(key=lambda task: task["key"])
    if len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("FRAMES identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} FRAMES questions to {out}")


if __name__ == "__main__":
    main()
