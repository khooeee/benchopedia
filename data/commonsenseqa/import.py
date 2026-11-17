"""Import the complete CommonsenseQA random-split validation set.

Run from the repository root: python3 data/commonsenseqa/import.py
PyArrow is needed only to read the pinned Parquet file, not to build the site.
The leaderboard test split is not imported: its reference answers are withheld.
"""

import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
DATASET = "tau/commonsense_qa"
EXPECTED_COUNT = 1221
LABELS = tuple("ABCDE")


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
        raise ValueError("CommonsenseQA validation file is empty")
    return parquet.read_table(io.BytesIO(payload)).to_pylist()


def to_task(row, index):
    task_id, question, choices, answer = (row.get(field) for field in
                                           ("id", "question", "choices", "answerKey"))
    where = f"row {index}"
    if not isinstance(task_id, str) or not re.fullmatch(r"[0-9a-f]{32}(?:_1)?", task_id):
        raise ValueError(f"{where}: unexpected task ID")
    if not isinstance(question, str) or not question.strip():
        raise ValueError(f"{task_id}: missing question")
    if not isinstance(choices, dict):
        raise ValueError(f"{task_id}: missing choices")
    labels, texts = choices.get("label"), choices.get("text")
    if labels != list(LABELS) or not isinstance(texts, list) or len(texts) != 5:
        raise ValueError(f"{task_id}: expected choices A through E")
    if any(not isinstance(text, str) or not text.strip() for text in texts):
        raise ValueError(f"{task_id}: empty choice")
    if answer not in LABELS:
        raise ValueError(f"{task_id}: missing reference answer")
    prompt = question + "\n\n" + "\n".join(f"{label}. {text}" for label, text in zip(labels, texts))
    source = f"https://huggingface.co/datasets/{DATASET}/viewer/default/validation?row={index}"
    return {
        "key": task_id,
        "prompt": prompt,
        "solution": f"{answer}. {texts[LABELS.index(answer)]}",
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable Hugging Face commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be the complete 1,221-question validation split.")
    tasks = [to_task(row, index) for index, row in enumerate(fetch_rows(revision))]
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("CommonsenseQA count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} CommonsenseQA validation tasks to {out}")


if __name__ == "__main__":
    main()
