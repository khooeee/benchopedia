#!/usr/bin/env python3
"""Import the Moral Stories action-only consequence-classification test split."""

import argparse
from collections import defaultdict
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.parse import quote
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
DATASET = "demelin/moral_stories"
FILENAME = "data/classification/consequence+action/minimal_pairs/test.jsonl"
CHECKSUM = "d9f5bf6811442bebb52ced6e46798ca9e2b1996d65c83a5e06972f066d4c183f"
TASK_ID = re.compile(r"[A-Z0-9]{30}[1-4]")
VARIANTS = {
    "1": ("moral_action", "moral_consequence", "1"),
    "2": ("moral_action", "immoral_consequence", "0"),
    "3": ("immoral_action", "immoral_consequence", "1"),
    "4": ("immoral_action", "moral_consequence", "0"),
}
LABELS = {"1": "plausible", "0": "implausible"}


def parse_rows(payload, source_url):
    tasks, seen, stories = [], set(), defaultdict(set)
    for number, line in enumerate(BytesIO(payload), start=1):
        row = json.loads(line)
        key = row["ID"]
        if not isinstance(key, str) or not TASK_ID.fullmatch(key) or key in seen:
            raise ValueError(f"Invalid or repeated Moral Stories key on line {number}")
        variant = key[-1]
        action_field, consequence_field, label = VARIANTS[variant]
        if row.keys() != {"ID", "label", action_field, consequence_field} or row["label"] != label:
            raise ValueError(f"{key}: action/consequence fields do not match the published variant")
        action, consequence = row[action_field], row[consequence_field]
        if not all(isinstance(value, str) and value.strip() for value in (action, consequence)):
            raise ValueError(f"{key}: missing action or consequence")
        tasks.append({
            "key": key,
            "prompt": f"Action\n{action}\n\nConsequence\n{consequence}",
            "solution": LABELS[label],
            "prompt_source_url": source_url,
            "solution_source_url": source_url,
        })
        seen.add(key)
        stories[key[:-1]].add(variant)
    if len(stories) != 1000 or any(variants != VARIANTS.keys() for variants in stories.values()):
        raise ValueError("Test split does not contain all four variants for each of 1,000 stories")
    return sorted(tasks, key=lambda task: task["key"])


def load_tasks(local_file=None):
    metadata = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = metadata["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must identify an immutable Hugging Face commit")
    dataset = f"https://huggingface.co/datasets/{DATASET}"
    relative = quote(FILENAME)
    if local_file is None:
        with urlopen(f"{dataset}/resolve/{revision}/{relative}", timeout=30) as response:
            payload = response.read()
    else:
        payload = local_file.read_bytes()
    if sha256(payload).hexdigest() != CHECKSUM:
        raise ValueError("Moral Stories test file checksum differs from the reviewed release")
    tasks = parse_rows(payload, f"{dataset}/blob/{revision}/{relative}")
    if len(tasks) != metadata["task_count"]:
        raise ValueError("Imported task count differs from benchmark.json")
    return tasks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-file", type=Path, help="Use a local copy of the pinned test file")
    args = parser.parse_args()
    tasks = load_tasks(args.local_file)
    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False) as temporary:
        for task in tasks:
            temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
    Path(temporary.name).replace(HERE / "tasks.jsonl")
    print(f"Imported {len(tasks):,} Moral Stories consequence pairs")


if __name__ == "__main__":
    main()
