#!/usr/bin/env python3
"""Import the complete BIG-Bench Mistake release for direct trace prediction."""

import argparse
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
REPOSITORY = "WHGTyen/BIG-Bench-Mistake"
TRACE_CHECKSUM = "da8d1d723e89f21e2a5579be19f361a83ecaacfc671e98935f51f533f0b4a80e"
PROMPT_CHECKSUM = "8d1344a4b2ce4162ddc96c55c13c41c66a2468905af67c786b0193da8960a7d5"
COUNTS = {
    "dyck_languages": (986, 650),
    "logical_deduction": (300, 294),
    "multistep_arithmetic": (300, 238),
    "tracking_shuffled_objects": (300, 260),
    "word_sorting": (300, 266),
}


def parse_tasks(payload, family, template, revision):
    source_file = f"https://github.com/{REPOSITORY}/blob/{revision}/{family}.jsonl"
    tasks, mistake_count = [], 0
    for line_number, line in enumerate(BytesIO(payload), start=1):
        row = json.loads(line)
        key = f"{family}-{line_number:04d}"
        question, steps, index = row["input"], row["steps"], row["mistake_index"]
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"{key}: missing source question")
        if not isinstance(steps, list) or not steps or any(not isinstance(step, str) for step in steps):
            raise ValueError(f"{key}: missing or invalid trace")
        if index is not None and (type(index) is not int or not 0 <= index < len(steps)):
            raise ValueError(f"{key}: first mistake index is outside the trace")
        numbered_steps = "\n".join(f"Thought {number}: {step}" for number, step in enumerate(steps, start=1))
        label = "No" if index is None else str(index + 1)
        mistake_count += index is not None
        source_url = f"{source_file}#L{line_number}"
        tasks.append({
            "key": key,
            "prompt": template.format(input=question, steps=numbered_steps),
            "solution": label,
            "prompt_source_url": source_url,
            "solution_source_url": source_url,
        })
    if (len(tasks), mistake_count) != COUNTS[family]:
        raise ValueError(f"{family}: task and mistake counts differ from the complete release")
    return tasks


def load_tasks(source_dir=None):
    metadata = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = metadata["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must identify an immutable GitHub commit")
    prompt_payload = (HERE / "direct-prompts.json").read_bytes()
    prompts = json.loads(prompt_payload)
    if prompts["source_revision"] != revision or sha256(prompt_payload).hexdigest() != PROMPT_CHECKSUM:
        raise ValueError("Direct prompts must match the reviewed release")
    tasks = []
    manifest = sha256()
    for family in sorted(COUNTS):
        name = f"{family}.jsonl"
        if source_dir is None:
            url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{name}"
            with urlopen(url, timeout=30) as response:
                payload = response.read()
        else:
            payload = (source_dir / name).read_bytes()
        manifest.update(f"{sha256(payload).hexdigest()}  {name}\n".encode())
        tasks.extend(parse_tasks(payload, family, prompts["conditions"][family]["template"], revision))
    if manifest.hexdigest() != TRACE_CHECKSUM:
        raise ValueError("Trace files differ from the reviewed release")
    if len(tasks) != metadata["task_count"] or len({task["key"] for task in tasks}) != len(tasks):
        raise ValueError("Imported task count or keys do not match the complete release")
    return tasks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, help="Read the five pinned trace files from this directory")
    args = parser.parse_args()
    tasks = load_tasks(args.source_dir)
    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False) as temporary:
        for task in tasks:
            temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
    Path(temporary.name).replace(HERE / "tasks.jsonl")
    print(f"Imported {len(tasks):,} BIG-Bench Mistake traces")


if __name__ == "__main__":
    main()
