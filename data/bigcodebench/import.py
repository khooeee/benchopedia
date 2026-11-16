"""Import all 1,140 BigCodeBench v0.1.4 tasks from their pinned Hugging Face revision.

Run from the repository root: python3 data/bigcodebench/import.py
PyArrow is needed only to read the pinned Parquet file, not to build the site.
"""

import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
DATASET = "bigcode/bigcodebench"
SPLIT = "v0.1.4"
EXPECTED_COUNT = 1140
# The evaluation harness, pinned separately for the environment link.
HARNESS = "bigcode-project/bigcodebench"
HARNESS_REVISION = "09dd993f46c3fbf3a799465bb96d524edcb0b199"
ENVIRONMENT_URL = f"https://github.com/{HARNESS}/blob/{HARNESS_REVISION}/Docker/Evaluate.Dockerfile"
FIELDS = ("task_id", "complete_prompt", "instruct_prompt", "canonical_solution", "test")


def fetch_rows(revision):
    try:
        import pyarrow.parquet as parquet
    except ImportError:
        sys.exit("This importer requires PyArrow. It is not used to build the site.")
    url = (f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/"
           f"data/{SPLIT}-00000-of-00001.parquet")
    with urllib.request.urlopen(url, timeout=120) as response:
        payload = response.read()
    if not payload:
        raise ValueError("Empty dataset file")
    return parquet.read_table(io.BytesIO(payload)).to_pylist()


def assemble_prompt(task_id, complete_prompt, instruct_prompt):
    """Show both official prompt formats; tilde fences keep their text intact."""
    for text in (complete_prompt, instruct_prompt):
        if re.search(r"^\s*~{3,}", text, re.M):
            raise ValueError(f"{task_id}: prompt contains a tilde fence")
    return (f"{task_id}\n\n## Complete prompt\n\n~~~python\n{complete_prompt}\n~~~\n\n"
            f"## Instruct prompt\n\n~~~text\n{instruct_prompt}\n~~~")


def to_task(index, row):
    task_id, complete_prompt, instruct_prompt, solution, test = (row.get(field) for field in FIELDS)
    if task_id != f"BigCodeBench/{index}":
        raise ValueError(f"Row {index}: unexpected task ID {task_id!r}")
    for field in FIELDS[1:]:
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError(f"{task_id}: missing {field}")
    if row.get("entry_point") != "task_func" or "class TestCases" not in test:
        raise ValueError(f"{task_id}: unexpected entry point or test layout")
    source = f"https://huggingface.co/datasets/{DATASET}/viewer/default/{SPLIT}?row={index}"
    return {
        "key": f"bigcodebench-{index:04d}",
        "prompt": assemble_prompt(task_id, complete_prompt, instruct_prompt),
        # The harness checks complete_prompt, a newline, and canonical_solution
        # against the test code appended after another newline.
        "solution": f"{complete_prompt}\n{solution}\n{test}",
        "prompt_source_url": source,
        "solution_source_url": source,
        "environment_url": ENVIRONMENT_URL,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable Hugging Face commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 1,140 BigCodeBench v0.1.4 tasks.")
    rows = fetch_rows(revision)
    if len(rows) != EXPECTED_COUNT:
        sys.exit(f"Expected {EXPECTED_COUNT} rows, found {len(rows)}.")
    tasks = [to_task(index, row) for index, row in enumerate(rows)]
    tasks.sort(key=lambda task: task["key"])
    if len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("BigCodeBench identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} BigCodeBench tasks to {out}")


if __name__ == "__main__":
    main()
