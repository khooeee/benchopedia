"""Import the complete BoolQ development split from its pinned dataset revision.

Run from the repository root: python3 data/boolq/import.py
PyArrow is needed only to read the pinned Parquet file, not to build the site.
The unlabeled test split is not part of this public mirror.
"""

import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
DATASET = "google/boolq"
EXPECTED_COUNT = 3270


def fetch_rows(revision):
    try:
        import pyarrow.parquet as parquet
    except ImportError:
        sys.exit("This importer requires PyArrow. It is not used to build the site.")
    url = (f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/"
           "data/validation-00000-of-00001.parquet")
    with urllib.request.urlopen(url, timeout=120) as response:
        payload = response.read()
    if not payload:
        raise ValueError("BoolQ development file is empty")
    return parquet.read_table(io.BytesIO(payload)).to_pylist()


def to_task(row, index):
    question, passage, answer = (row.get(field) for field in ("question", "passage", "answer"))
    where = f"row {index}"
    if not isinstance(question, str) or not question.strip():
        raise ValueError(f"{where}: missing question")
    if not isinstance(passage, str) or not passage.strip():
        raise ValueError(f"{where}: missing passage")
    if type(answer) is not bool:
        raise ValueError(f"{where}: missing yes/no answer")
    source = f"https://huggingface.co/datasets/{DATASET}/viewer/default/validation?row={index}"
    return {
        "key": f"boolq-{index + 1:04d}",
        "prompt": question + "\n\n" + passage,
        "solution": "yes" if answer else "no",
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable Hugging Face commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be the complete 3,270-example development split.")
    tasks = [to_task(row, index) for index, row in enumerate(fetch_rows(revision))]
    tasks.sort(key=lambda task: task["key"])
    expected = {f"boolq-{index:04d}" for index in range(1, EXPECTED_COUNT + 1)}
    if len(tasks) != EXPECTED_COUNT or {task["key"] for task in tasks} != expected:
        sys.exit("BoolQ count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} BoolQ development tasks to {out}")


if __name__ == "__main__":
    main()
