"""Import MMLU's complete all/test split, including choices and reference answers.

Download the exact Parquet file at benchmark.json's dataset revision. PyArrow is
needed only for this importer, not for building or serving the site.
"""

import io
import json
import re
import sys
import urllib.request
from pathlib import Path

DATASET = "cais/mmlu"
CONFIG = "all"
SPLIT = "test"
LETTERS = "ABCD"
BENCHMARK_DIR = Path(__file__).resolve().parent


def fetch_rows(revision):
    try:
        import pyarrow.parquet as parquet
    except ImportError:
        sys.exit("This importer requires PyArrow; see the MMLU import instructions in README.md.")
    url = f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/{CONFIG}/{SPLIT}-00000-of-00001.parquet"
    with urllib.request.urlopen(url, timeout=60) as response:
        payload = response.read()
    return parquet.read_table(io.BytesIO(payload)).to_pylist()


def to_task(item):
    row, index = item["row"], item["row_idx"]
    question, choices, answer, subject = (row[key] for key in ("question", "choices", "answer", "subject"))
    if not isinstance(question, str) or not question.strip():
        raise ValueError(f"Row {index}: missing task text")
    if (not isinstance(choices, list) or len(choices) != 4
            or any(not isinstance(choice, str) or not choice.strip() for choice in choices)):
        raise ValueError(f"Row {index}: expected four nonempty choices")
    if type(answer) is not int or not 0 <= answer < 4:
        raise ValueError(f"Row {index}: invalid reference answer index")
    if not isinstance(subject, str) or not re.fullmatch(r"[a-z0-9_]+", subject):
        raise ValueError(f"Row {index}: invalid subject")
    if type(index) is not int or index < 0:
        raise ValueError("Invalid upstream row index")
    # IDs use the one-based row position in the pinned all/test split, not a
    # subject-local position. The source viewer uses the zero-based row index.
    source = f"https://huggingface.co/datasets/{DATASET}/viewer/{CONFIG}/{SPLIT}?row={index}"
    return {
        "key": f"{subject}-test-{index + 1:05d}",
        "prompt": question + "\n\n" + "\n".join(f"{letter}. {choice}" for letter, choice in zip(LETTERS, choices)),
        "solution": f"{LETTERS[answer]}. {choices[answer]}",
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision, count = benchmark["dataset_revision"], benchmark["task_count"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable Hugging Face commit SHA.")
    rows = fetch_rows(revision)
    items = [{"row_idx": index, "row": row} for index, row in enumerate(rows)]
    tasks = sorted((to_task(item) for item in items), key=lambda task: task["key"])
    subjects = {item["row"]["subject"] for item in items}
    if len(tasks) != count or len({task["key"] for task in tasks}) != count or len(subjects) != 57:
        sys.exit("MMLU count, identifiers, or subject coverage differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as stream:
        for task in tasks:
            stream.write(json.dumps(task, ensure_ascii=False) + "\n")
    temporary.replace(out)
    print(f"Wrote {len(tasks):,} tasks across {len(subjects)} subjects to {out}")


if __name__ == "__main__":
    main()
