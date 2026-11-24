#!/usr/bin/env python3
"""Import the paired zero-shot abduction and deduction tests."""

import argparse
from collections import Counter
import csv
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
REPOSITORY = "kmineshima/abduction-syllogism-llm"
SPLITS = {
    "abduction": (
        "Abduction_synthetic_problems.tsv",
        "402fea452519318e3fd1daaa8ec96d2880a571b6b543cb4c1778110bbe27287c",
        "Rule", "Observation", "Neither is a good explanation.",
    ),
    "deduction": (
        "Deduction_synthetic_problems.tsv",
        "187c3891b9368dcb8a7f377a870e03bb3fc631d20f45aa82c39912b678945c43",
        "P1", "P2", "Neither.",
    ),
}
DIRECTIONS = {
    "abduction": "Select the hypothesis that best explains the observation under the supplied rule. The observation should follow from the rule together with the hypothesis.",
    "deduction": "Select the conclusion that follows logically from the two given premises.",
}
CONTENT_COUNTS = {"consistent": 66, "inconsistent": 66, "neutral": 84}
LABEL_COUNTS = {"abduction": {"1": 81, "2": 27, "3": 108}, "deduction": {"1": 27, "2": 81, "3": 108}}


def parse_cases(payload, mode, revision):
    name, _, first_label, second_label, neither = SPLITS[mode]
    source_url = f"https://github.com/{REPOSITORY}/blob/{revision}/data/{name}"
    rows = csv.DictReader(StringIO(payload.decode("utf-8"), newline=""), delimiter="\t")
    cases, indices, labels, contents = [], set(), Counter(), Counter()
    for row in rows:
        index = int(row[""])
        if index in indices:
            raise ValueError(f"{mode}: repeated source index {index}")
        indices.add(index)
        key = f"{index:03d}-{mode}"
        first, separator, second = row["premises_en"].partition(". ")
        if not first or not separator or not second or ". " in second:
            raise ValueError(f"{key}: expected exactly two source sentences")
        choices = (row["hypothesis_en_1"], row["hypothesis_en_2"], neither)
        label, content = row["gold"], row["content"]
        if label not in ("1", "2", "3") or not all(choice.strip() for choice in choices):
            raise ValueError(f"{key}: missing choices or reference label")
        numbered = "\n".join(f"{number}. {choice}" for number, choice in enumerate(choices, start=1))
        prompt = f"{DIRECTIONS[mode]}\n\n{first_label}: {first}.\n{second_label}: {second}\n\n{numbered}"
        task_link = f"{source_url}#L{rows.line_num}"
        task = {
            "key": key,
            "prompt": prompt,
            "solution": f"{label}. {choices[int(label) - 1]}",
            "prompt_source_url": task_link,
            "solution_source_url": task_link,
        }
        cases.append((task, content))
        labels[label] += 1
        contents[content] += 1
    if indices != set(range(216)) or labels != LABEL_COUNTS[mode] or contents != CONTENT_COUNTS:
        raise ValueError(f"{mode}: indices or reference categories differ from the complete release")
    return cases


def load_cases(source_dir=None):
    metadata = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = metadata["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must identify an immutable GitHub commit")
    cases = []
    for mode, (name, checksum, *_prompt_labels) in SPLITS.items():
        if source_dir is None:
            url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/data/{name}"
            with urlopen(url, timeout=30) as response:
                payload = response.read()
        else:
            payload = (source_dir / name).read_bytes()
        if sha256(payload).hexdigest() != checksum:
            raise ValueError(f"{name}: file differs from the reviewed release")
        cases.extend(parse_cases(payload, mode, revision))
    if len(cases) != metadata["task_count"]:
        raise ValueError("Imported task count differs from benchmark.json")
    return sorted(cases, key=lambda case: case[0]["key"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, help="Use local copies of both pinned TSVs")
    args = parser.parse_args()
    cases = load_cases(args.source_dir)
    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False) as temporary:
        for task, _ in cases:
            temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
    Path(temporary.name).replace(HERE / "tasks.jsonl")
    print(f"Imported {len(cases):,} paired syllogism tasks")


if __name__ == "__main__":
    main()
