#!/usr/bin/env python3
"""Import every systematicity and productivity test pair from PCFG SET."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from eval import SEQUENCE


HERE = Path(__file__).resolve().parent
REPOSITORY = "i-machine-think/am-i-compositional"
DATA_DIRECTORY = "data/pcfgset"
SPLITS = {
    "productivity": 11333,
    "systematicity": 10175,
}
CHECKSUMS = {
    "productivity/test.src": "ba03bc5c468e955d537c06ca02c900c431a16f37b8b3f02e5eaa8a93434a3f73",
    "productivity/test.tgt": "55704b1e887ffeffb104fc1ba4bc44dd6b0e95e34a355bd07d86881fd226a254",
    "systematicity/test.src": "9c47ccf869899e65c2c2cf530403c8fefdcb5de57787c9ff029dc7d9b8018941",
    "systematicity/test.tgt": "2896474cdeb151929bd85ed10aeeca37866e11dafa00f62e1660804f0dfc5a8a",
}


def metadata():
    return json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))


def read_lines(path, raw_url, local_dir):
    if local_dir is None:
        with urlopen(f"{raw_url}/{path}", timeout=30) as response:
            payload = response.read()
    else:
        payload = (local_dir / path).read_bytes()
    if sha256(payload).hexdigest() != CHECKSUMS[path]:
        raise ValueError(f"{path}: checksum differs from the reviewed snapshot")
    return payload.decode("utf-8").splitlines()


def load_tasks(local_dir=None):
    config = metadata()
    revision = config["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must identify an immutable Git commit")
    raw = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{DATA_DIRECTORY}"
    web = f"https://github.com/{REPOSITORY}/blob/{revision}/{DATA_DIRECTORY}"
    tasks = []
    for split, count in SPLITS.items():
        prompts = read_lines(f"{split}/test.src", raw, local_dir)
        answers = read_lines(f"{split}/test.tgt", raw, local_dir)
        if len(prompts) != count or len(answers) != count:
            raise ValueError(f"{split}: expected {count} aligned test pairs")
        for line, (prompt, answer) in enumerate(zip(prompts, answers), start=1):
            if not prompt.strip() or not SEQUENCE.fullmatch(answer) or " ".join(answer.split()) != answer:
                raise ValueError(f"{split}:{line}: incomplete expression or target sequence")
            tasks.append({
                "key": f"{split}-{line:05d}",
                "prompt": prompt,
                "solution": answer,
                "prompt_source_url": f"{web}/{split}/test.src",
                "solution_source_url": f"{web}/{split}/test.tgt",
            })
    if len(tasks) != config["task_count"]:
        raise ValueError("Imported task count differs from benchmark.json")
    return tasks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-dir", type=Path, help="Use local copies of the four checksum-pinned files")
    args = parser.parse_args()
    tasks = load_tasks(args.local_dir)
    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False) as temporary:
        for task in tasks:
            temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
    Path(temporary.name).replace(HERE / "tasks.jsonl")
    print(f"Imported {len(tasks):,} PCFG SET test records")


if __name__ == "__main__":
    main()
