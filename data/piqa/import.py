# Regenerates tasks.jsonl for PIQA's validation split.
# Run from the repository root: python3 data/piqa/import.py

import json
import re
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parent
BENCHMARK = json.loads((DATA / "benchmark.json").read_text())
REVISION = BENCHMARK["dataset_revision"]
RAW = f"https://raw.githubusercontent.com/ybisk/ybisk.github.io/{REVISION}/piqa/data"
BLOB = f"https://github.com/ybisk/ybisk.github.io/blob/{REVISION}/piqa/data"
EXPECTED_COUNT = 1838


def fetch(name):
    with urlopen(f"{RAW}/{name}", timeout=120) as response:
        return response.read()


def main():
    if not re.fullmatch(r"[0-9a-f]{40}", REVISION):
        raise SystemExit("dataset_revision must be a 40-character commit")
    rows = [
        json.loads(line)
        for line in fetch("valid.jsonl").decode("utf-8").splitlines()
        if line.strip()
    ]
    labels = [
        line.strip()
        for line in fetch("valid-labels.lst").decode("utf-8").splitlines()
        if line.strip()
    ]
    if len(rows) != EXPECTED_COUNT or len(labels) != EXPECTED_COUNT:
        raise SystemExit(f"expected {EXPECTED_COUNT} rows and labels, got {len(rows)} and {len(labels)}")
    tasks = []
    for index, (row, label) in enumerate(zip(rows, labels), start=1):
        if set(row) != {"goal", "sol1", "sol2"}:
            raise SystemExit(f"row {index} has unexpected fields: {sorted(row)}")
        goal, first, second = row["goal"], row["sol1"], row["sol2"]
        if not all(isinstance(value, str) and value.strip() for value in (goal, first, second)):
            raise SystemExit(f"row {index} has an empty field")
        if any("\r" in value or "\n" in value for value in (goal, first, second)):
            raise SystemExit(f"row {index} contains a newline")
        if label not in {"0", "1"}:
            raise SystemExit(f"row {index} has label {label!r}")
        chosen = first if label == "0" else second
        number = "1" if label == "0" else "2"
        tasks.append({
            "key": f"piqa-{index:04d}",
            "prompt": f"{goal}\n\n1. {first}\n2. {second}",
            "solution": f"{number}. {chosen}",
            "prompt_source_url": f"{BLOB}/valid.jsonl#L{index}",
            "solution_source_url": f"{BLOB}/valid-labels.lst#L{index}",
        })
    keys = [item["key"] for item in tasks]
    if len(set(keys)) != len(keys):
        raise SystemExit("duplicate keys")
    destination = DATA / "tasks.jsonl"
    temporary = destination.with_suffix(".jsonl.tmp")
    try:
        temporary.write_text(
            "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in tasks),
            encoding="utf-8",
        )
        temporary.replace(destination)
    finally:
        if temporary.exists():
            temporary.unlink()
    print(f"wrote {len(tasks)} tasks to {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
