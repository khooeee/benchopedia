#!/usr/bin/env python3
"""Import the pinned QuaRTz question-only test split from AllenAI."""

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
DATASET = "allenai/quartz"
FILENAME = "data/test-00000-of-00001.parquet"
TEST_SHA256 = "78c4c77cfc1ad0e65dbdfeec4ed788117e73484ad44f6a2aebf43e08c7fba2e8"
TASK_ID = re.compile(r"QRQA-\d+-\d+(?:-flip)?")


def metadata():
    return json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))


def load_tasks(local_path=None):
    config = metadata()
    revision = config["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must identify an immutable Hugging Face commit")
    dataset = f"https://huggingface.co/datasets/{DATASET}"
    if local_path is None:
        with urlopen(f"{dataset}/resolve/{revision}/{FILENAME}", timeout=30) as response:
            payload = response.read()
    else:
        payload = local_path.read_bytes()
    if sha256(payload).hexdigest() != TEST_SHA256:
        raise ValueError("QuaRTz test file checksum differs from the reviewed snapshot")

    rows = parquet.read_table(
        BytesIO(payload), columns=["id", "question", "choices", "answerKey"],
    ).to_pylist()
    source = f"{dataset}/blob/{revision}/{FILENAME}"
    tasks, labels = [], {}
    for row in rows:
        key, question, choices, answer = (row[name] for name in ("id", "question", "choices", "answerKey"))
        if not isinstance(key, str) or not TASK_ID.fullmatch(key) or key in labels:
            raise ValueError(f"Invalid or repeated QuaRTz ID {key!r}")
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"{key}: missing question")
        if (not isinstance(choices, dict) or choices.get("label") != ["A", "B"]
                or not isinstance(choices.get("text"), list) or len(choices["text"]) != 2
                or not all(isinstance(text, str) and text.strip() for text in choices["text"])
                or answer not in ("A", "B")):
            raise ValueError(f"{key}: invalid choices or answer key")
        options = dict(zip(choices["label"], choices["text"]))
        tasks.append({
            "key": key,
            "prompt": f"{question}\n\nA. {options['A']}\nB. {options['B']}",
            "solution": f"{answer}. {options[answer]}",
            "prompt_source_url": source,
            "solution_source_url": source,
        })
        labels[key] = answer

    original = {key for key in labels if not key.endswith("-flip")}
    flipped = {key[:-5] for key in labels if key.endswith("-flip")}
    if (len(tasks) != config["task_count"] or original != flipped
            or any(labels[key] == labels[f"{key}-flip"] for key in original)):
        raise ValueError("Expected the complete published test split with paired opposite labels")
    return sorted(tasks, key=lambda task: task["key"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-file", type=Path, help="Use a local copy of the checksum-pinned test file")
    args = parser.parse_args()
    tasks = load_tasks(args.local_file)
    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False) as temporary:
        for task in tasks:
            temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
    Path(temporary.name).replace(HERE / "tasks.jsonl")
    print(f"Imported {len(tasks):,} QuaRTz test questions")


if __name__ == "__main__":
    main()
