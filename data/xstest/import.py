"""Import all 450 XSTest prompts from their pinned GitHub commit.

Run from the repository root: python3 data/xstest/import.py
Only Python's standard library is required.
"""

import csv
import io
import json
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "paul-rottger/xstest"
SOURCE_PATH = "xstest_prompts.csv"
COLUMNS = ["id", "prompt", "type", "label", "focus", "note"]
PROMPTS_PER_TYPE = 25
SAFE_TYPES = 10
UNSAFE_TYPES = 8
EXPECTED_COUNT = PROMPTS_PER_TYPE * (SAFE_TYPES + UNSAFE_TYPES)


def fetch_rows(revision):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{SOURCE_PATH}"
    with urllib.request.urlopen(url, timeout=60) as response:
        text = response.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(text, newline=""))
    if reader.fieldnames != COLUMNS:
        raise ValueError(f"Unexpected columns: {reader.fieldnames}")
    # Keep each record's starting line for its source link.
    rows, line = [], reader.line_num + 1
    for row in reader:
        rows.append((line, row))
        line = reader.line_num + 1
    return rows


def to_task(line, row, revision):
    where = f"Line {line}"
    if not row["id"].isdigit() or not row["prompt"].strip() or not row["type"]:
        raise ValueError(f"{where}: missing ID, prompt, or type")
    # The README marks prompts whose type starts with contrast_ as unsafe.
    expected = "unsafe" if row["type"].startswith("contrast_") else "safe"
    if row["label"] != expected:
        raise ValueError(f"{where}: label {row['label']!r} does not match type {row['type']!r}")
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{SOURCE_PATH}?plain=1#L{line}"
    return {
        "key": f"{int(row['id']):03d}-{row['type']}",
        "prompt": row["prompt"],
        "solution": row["label"],
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 450 XSTest prompts.")
    rows = fetch_rows(revision)
    tasks = [to_task(line, row, revision) for line, row in rows]
    types = Counter(row["type"] for _, row in rows)
    unsafe = sum(1 for kind in types if kind.startswith("contrast_"))
    if (len(types) - unsafe, unsafe) != (SAFE_TYPES, UNSAFE_TYPES) or set(types.values()) != {PROMPTS_PER_TYPE}:
        sys.exit("XSTest prompt types differ from 10 safe and 8 unsafe types of 25 prompts each.")
    if sorted(int(row["id"]) for _, row in rows) != list(range(1, EXPECTED_COUNT + 1)):
        sys.exit("XSTest IDs must run from 1 through 450.")
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("XSTest count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} XSTest prompts to {out}")


if __name__ == "__main__":
    main()
