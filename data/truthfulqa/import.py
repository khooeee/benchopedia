"""Import all 817 TruthfulQA generation questions and reference-answer fields.

Run from the repository root: python3 data/truthfulqa/import.py
Uses only Python's standard library. An intentional source update requires
reviewing the license and updating dataset_revision and SOURCE_SHA256 together.
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
REPOSITORY = "sylinrl/TruthfulQA"
SOURCE_PATH = "TruthfulQA.csv"
SOURCE_SHA256 = "f9bd9e859cc102cb1f647f1064da7e009be752c416845cf9fa56e6eaae403a7d"
EXPECTED_COUNT = 817
FIELDS = ("Type", "Category", "Question", "Best Answer", "Correct Answers",
          "Incorrect Answers", "Source")


def fetch_source(revision):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{SOURCE_PATH}"
    with urllib.request.urlopen(url, timeout=60) as response:
        content = response.read()
    if hashlib.sha256(content).hexdigest() != SOURCE_SHA256:
        raise ValueError("TruthfulQA checksum differs from the reviewed generation set")
    return content


def parse_rows(content):
    # The official CSV starts with a UTF-8 BOM. newline='' lets csv preserve
    # embedded newlines and track physical source lines for record permalinks.
    with io.StringIO(content.decode("utf-8-sig"), newline="") as stream:
        reader = csv.DictReader(stream, strict=True)
        if reader.fieldnames != list(FIELDS):
            raise ValueError("TruthfulQA CSV columns differ from the reviewed format")
        previous_line = reader.line_num
        rows = []
        for row in reader:
            rows.append((row, previous_line + 1, reader.line_num))
            previous_line = reader.line_num
    return rows


def to_task(row, index, first_line, last_line, revision):
    if not isinstance(row, dict) or set(row) != set(FIELDS):
        raise ValueError(f"Record {index}: missing or extra CSV fields")
    if any(not isinstance(row[field], str) for field in FIELDS):
        raise ValueError(f"Record {index}: missing CSV value")
    if any(not row[field].strip() for field in FIELDS if field != "Source"):
        raise ValueError(f"Record {index}: missing question or reference answers")
    if row["Type"] not in ("Adversarial", "Non-Adversarial"):
        raise ValueError(f"Record {index}: unrecognized question type")
    correct = {answer.strip() for answer in row["Correct Answers"].split(";")}
    if row["Best Answer"].strip() not in correct:
        raise ValueError(f"Record {index}: best answer is absent from correct references")
    blocks = [
        "Best answer (upstream):\n" + row["Best Answer"],
        "Correct reference answers (semicolon-separated):\n" + row["Correct Answers"],
        "Incorrect reference answers (negative examples; false or misleading):\n"
        + row["Incorrect Answers"],
    ]
    if row["Source"].strip():
        blocks.append("Supporting source cited upstream:\n" + row["Source"])
    fragment = f"L{first_line}" if first_line == last_line else f"L{first_line}-L{last_line}"
    source = (f"https://github.com/{REPOSITORY}/blob/{revision}/"
              f"{SOURCE_PATH}?plain=1#{fragment}")
    return {
        "key": f"generation-{index:04d}",
        "prompt": row["Question"],
        "solution": "\n\n".join(blocks),
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT or benchmark["has_solutions"] is not True:
        sys.exit("Scope must be all 817 generation tasks with reference answers.")
    rows = parse_rows(fetch_source(revision))
    tasks = [to_task(row, index, first, last, revision)
             for index, (row, first, last) in enumerate(rows, 1)]
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("TruthfulQA task count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} TruthfulQA generation tasks to {out}")


if __name__ == "__main__":
    main()
