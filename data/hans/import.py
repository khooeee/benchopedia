#!/usr/bin/env python3
"""Import the complete evaluation set from the original HANS release."""

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
REPOSITORY = "tommccoy1/hans"
FILENAME = "heuristics_evaluation_set.txt"
CHECKSUM = "c55b62feef9913070e88f38938dc2492018c945ac81f70139346472494124e79"
HEURISTICS = ("lexical_overlap", "subsequence", "constituent")
LABELS = ("entailment", "non-entailment")


def parse_evaluation(payload, source_url):
    tasks, categories = [], {}
    heuristic_counts, subcase_counts = Counter(), Counter()
    with StringIO(payload.decode("utf-8"), newline="") as table:
        rows = csv.DictReader(table, delimiter="\t", quoting=csv.QUOTE_NONE)
        for index, row in enumerate(rows):
            key = row["pairID"]
            label = row["gold_label"]
            group = (row["heuristic"], row["subcase"], row["template"])
            premise, hypothesis = row["sentence1"], row["sentence2"]
            if (None in row or key != f"ex{index}" or label not in LABELS
                    or group[0] not in HEURISTICS
                    or not all(value and value == value.strip() for value in (premise, hypothesis, *group))):
                raise ValueError(f"Invalid HANS source record on line {index + 2}")
            source = f"{source_url}#L{index + 2}"
            tasks.append({
                "key": key,
                "prompt": f"Premise\n{premise}\n\nHypothesis\n{hypothesis}",
                "solution": label,
                "prompt_source_url": source,
                "solution_source_url": source,
            })
            categories[key] = group
            heuristic_counts[group[0], label] += 1
            subcase_counts[group[0], group[1]] += 1
    balanced = {(name, label): 5000 for name in HEURISTICS for label in LABELS}
    subcases = Counter(heuristic for heuristic, _ in subcase_counts)
    if (heuristic_counts != balanced or set(subcase_counts.values()) != {1000}
            or subcases != {name: 10 for name in HEURISTICS}):
        raise ValueError("HANS evaluation groups differ from the complete published test split")
    return tasks, categories


def load_evaluation(local_file=None):
    metadata = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = metadata["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must identify an immutable Git commit")
    if local_file is None:
        url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{FILENAME}"
        with urlopen(url, timeout=60) as response:
            payload = response.read()
    else:
        payload = local_file.read_bytes()
    if sha256(payload).hexdigest() != CHECKSUM:
        raise ValueError("HANS evaluation file checksum differs from the reviewed snapshot")
    web = f"https://github.com/{REPOSITORY}/blob/{revision}/{FILENAME}"
    tasks, categories = parse_evaluation(payload, web)
    if len(tasks) != metadata["task_count"]:
        raise ValueError("Imported task count differs from benchmark.json")
    return tasks, categories


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-file", type=Path, help="Use a local copy of the checksum-pinned test file")
    args = parser.parse_args()
    tasks, _ = load_evaluation(args.local_file)
    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False) as temporary:
        for task in tasks:
            temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
    Path(temporary.name).replace(HERE / "tasks.jsonl")
    print(f"Imported {len(tasks):,} HANS evaluation pairs")


if __name__ == "__main__":
    main()
