#!/usr/bin/env python3
"""Import the complete QASC development split in the question-only setting."""

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from pyarrow import parquet


HERE = Path(__file__).resolve().parent
DATASET = "allenai/qasc"
FILENAME = "data/validation-00000-of-00001.parquet"
CHECKSUM = "d1ae34ae13c5fce2c55305372c203c6cdb789728d0d7e5ea2956d55bc33f40ae"
LABELS = list("ABCDEFGH")
TASK_ID = re.compile(r"[0-9A-Z]{30}")


def load_tasks(local_file=None):
    metadata = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = metadata["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must identify an immutable Hugging Face commit")
    dataset = f"https://huggingface.co/datasets/{DATASET}"
    if local_file is None:
        with urlopen(f"{dataset}/resolve/{revision}/{FILENAME}", timeout=30) as response:
            payload = response.read()
    else:
        payload = local_file.read_bytes()
    if sha256(payload).hexdigest() != CHECKSUM:
        raise ValueError("QASC development file checksum differs from the reviewed release")

    inputs = parquet.read_table(
        BytesIO(payload), columns=["id", "question", "choices", "answerKey"],
    ).to_pylist()
    tasks, seen = [], set()
    source = f"{dataset}/blob/{revision}/{FILENAME}"
    for row in inputs:
        key, question, choices, answer = (row[name] for name in ("id", "question", "choices", "answerKey"))
        if not isinstance(key, str) or not TASK_ID.fullmatch(key) or key in seen:
            raise ValueError(f"Invalid or repeated QASC record ID {key!r}")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"{key}: missing question")
        if (not isinstance(choices, dict) or choices.get("label") != LABELS
                or not isinstance(choices.get("text"), list) or len(choices["text"]) != len(LABELS)
                or not all(isinstance(text, str) and text.strip() for text in choices["text"])
                or answer not in LABELS):
            raise ValueError(f"{key}: invalid answer choices or answer key")
        options = dict(zip(choices["label"], choices["text"]))
        prompt = question + "\n\n" + "\n".join(f"{label}. {text}" for label, text in options.items())
        tasks.append({
            "key": key,
            "prompt": prompt,
            "solution": f"{answer}. {options[answer]}",
            "prompt_source_url": source,
            "solution_source_url": source,
        })
        seen.add(key)
    if len(tasks) != metadata["task_count"]:
        raise ValueError("Imported task count differs from benchmark.json")
    return sorted(tasks, key=lambda task: task["key"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-file", type=Path, help="Use a local copy of the pinned development file")
    args = parser.parse_args()
    tasks = load_tasks(args.local_file)
    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False) as temporary:
        for task in tasks:
            temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
    Path(temporary.name).replace(HERE / "tasks.jsonl")
    print(f"Imported {len(tasks):,} QASC development questions")


if __name__ == "__main__":
    main()
