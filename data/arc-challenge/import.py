"""Import the complete ARC-Challenge test split from its pinned dataset revision.

Run from the repository root: python3 data/arc-challenge/import.py
PyArrow is needed only to read the pinned Parquet file, not to build the site.
"""

import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
DATASET = "allenai/ai2_arc"
CONFIG = "ARC-Challenge"
EXPECTED_COUNT = 1172


def fetch_rows(revision):
    try:
        import pyarrow.parquet as parquet
    except ImportError:
        sys.exit("This importer requires PyArrow. It is not used to build the site.")
    url = (f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/"
           f"{CONFIG}/test-00000-of-00001.parquet")
    with urllib.request.urlopen(url, timeout=120) as response:
        payload = response.read()
    if not payload:
        raise ValueError("ARC-Challenge test file is empty")
    return parquet.read_table(io.BytesIO(payload)).to_pylist()


def to_task(row, index, revision):
    question, choices, answer, task_id = (row.get(field) for field in
                                           ("question", "choices", "answerKey", "id"))
    where = f"row {index}"
    if not isinstance(task_id, str) or not task_id.strip() or task_id != task_id.strip():
        raise ValueError(f"{where}: missing task ID")
    if not isinstance(question, str) or not question.strip():
        raise ValueError(f"{task_id}: missing question")
    if not isinstance(choices, dict):
        raise ValueError(f"{task_id}: missing choices")
    labels, texts = choices.get("label"), choices.get("text")
    if (not isinstance(labels, list) or not isinstance(texts, list)
            or len(labels) not in (3, 4, 5) or len(texts) != len(labels)
            or any(not isinstance(label, str) or not label.strip() for label in labels)
            or any(not isinstance(text, str) or not text.strip() for text in texts)):
        raise ValueError(f"{task_id}: expected three to five labeled choices")
    if len(set(labels)) != len(labels):
        raise ValueError(f"{task_id}: duplicate choice labels")
    if not isinstance(answer, str) or answer not in labels:
        raise ValueError(f"{task_id}: answer does not match a choice label")
    answer_text = texts[labels.index(answer)]
    prompt = question + "\n\n" + "\n".join(f"{label}. {text}" for label, text in zip(labels, texts))
    source = f"https://huggingface.co/datasets/{DATASET}/viewer/{CONFIG}/test?row={index}"
    return {
        "key": task_id,
        "prompt": prompt,
        "solution": f"{answer}. {answer_text}",
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable Hugging Face commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be the complete 1,172-question Challenge test split.")
    rows = fetch_rows(revision)
    tasks = [to_task(row, index, revision) for index, row in enumerate(rows)]
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("ARC-Challenge count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} ARC-Challenge test tasks to {out}")


if __name__ == "__main__":
    main()
