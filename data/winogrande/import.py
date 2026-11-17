# Regenerates tasks.jsonl for WinoGrande's development split.
# Run from the repository root: python3 data/winogrande/import.py

import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parent
BENCHMARK = json.loads((DATA / "benchmark.json").read_text())
SOURCE_URL = BENCHMARK["dataset_url"]
SOURCE_SHA256 = BENCHMARK["dataset_revision"]
DEV_PATH = "winogrande_1.1/dev.jsonl"
LABEL_PATH = "winogrande_1.1/dev-labels.lst"
EXPECTED_COUNT = 1267
KEY_PATTERN = re.compile(r"^[0-9A-Z-]{32}$")


def load_zip():
    if not re.fullmatch(r"[0-9a-f]{64}", SOURCE_SHA256):
        raise SystemExit("dataset_revision must be the zip SHA-256")
    with urlopen(SOURCE_URL, timeout=120) as response:
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != SOURCE_SHA256:
        raise SystemExit(f"checksum mismatch: {digest}")
    archive = zipfile.ZipFile(io.BytesIO(payload))
    rows = [
        json.loads(line)
        for line in archive.read(DEV_PATH).decode("utf-8").splitlines()
        if line.strip()
    ]
    labels = [
        line.strip()
        for line in archive.read(LABEL_PATH).decode("utf-8").splitlines()
        if line.strip()
    ]
    return rows, labels


def task(row, label):
    if set(row) != {"qID", "sentence", "option1", "option2", "answer"}:
        raise SystemExit(f"unexpected fields: {sorted(row)}")
    key = row["qID"]
    sentence = row["sentence"]
    option1 = row["option1"]
    option2 = row["option2"]
    answer = row["answer"]
    if not KEY_PATTERN.fullmatch(key):
        raise SystemExit(f"unexpected question id: {key!r}")
    if not isinstance(sentence, str) or not sentence.strip():
        raise SystemExit(f"{key} has an empty sentence")
    if not isinstance(option1, str) or not option1.strip():
        raise SystemExit(f"{key} has an empty first option")
    if not isinstance(option2, str) or not option2.strip():
        raise SystemExit(f"{key} has an empty second option")
    if answer not in {"1", "2"} or answer != label:
        raise SystemExit(f"{key} answer {answer!r} does not match label {label!r}")
    if "\r" in sentence or "\r" in option1 or "\r" in option2:
        raise SystemExit(f"{key} contains a carriage return")
    chosen = option1 if answer == "1" else option2
    return {
        "key": key,
        "prompt": f"{sentence}\n\n1. {option1}\n2. {option2}",
        "solution": f"{answer}. {chosen}",
        "prompt_source_url": SOURCE_URL,
        "solution_source_url": SOURCE_URL,
    }


def main():
    rows, labels = load_zip()
    if len(rows) != EXPECTED_COUNT or len(labels) != EXPECTED_COUNT:
        raise SystemExit(f"expected {EXPECTED_COUNT} rows and labels, got {len(rows)} and {len(labels)}")
    tasks = [task(row, label) for row, label in zip(rows, labels)]
    keys = [item["key"] for item in tasks]
    if len(set(keys)) != len(keys):
        raise SystemExit("duplicate question ids")
    tasks.sort(key=lambda item: item["key"])
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
