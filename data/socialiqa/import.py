# Regenerates tasks.jsonl for SocialIQA's version 1.4 test split.
# Run from the repository root: python3 data/socialiqa/import.py

import hashlib
import io
import json
import re
import tarfile
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(__file__).resolve().parent
BENCHMARK = json.loads((DATA / "benchmark.json").read_text())
SOURCE_URL = BENCHMARK["dataset_url"]
SOURCE_SHA256 = BENCHMARK["dataset_revision"]
TEST_PATH = "socialIQa_v1.4_tst.jsonl"
EXPECTED_COUNT = 2224
FIELDS = {"context", "question", "answerA", "answerB", "answerC", "correct"}


def load_rows():
    if not re.fullmatch(r"[0-9a-f]{64}", SOURCE_SHA256):
        raise SystemExit("dataset_revision must be the archive SHA-256")
    with urlopen(SOURCE_URL, timeout=120) as response:
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != SOURCE_SHA256:
        raise SystemExit(f"checksum mismatch: {digest}")
    archive = tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz")
    return [
        json.loads(line)
        for line in archive.extractfile(TEST_PATH).read().decode("utf-8").splitlines()
        if line.strip()
    ]


def task(index, row):
    if set(row) != FIELDS:
        raise SystemExit(f"row {index} has unexpected fields: {sorted(row)}")
    context = row["context"]
    question = row["question"]
    answers = {"A": row["answerA"], "B": row["answerB"], "C": row["answerC"]}
    letter = row["correct"]
    if letter not in answers:
        raise SystemExit(f"row {index} has answer {letter!r}")
    values = [context, question, *answers.values()]
    if not all(isinstance(value, str) and value.strip() for value in values):
        raise SystemExit(f"row {index} has an empty field")
    if any("\r" in value for value in values):
        raise SystemExit(f"row {index} contains a carriage return")
    choices = "\n".join(f"{choice}. {answers[choice]}" for choice in "ABC")
    return {
        "key": f"socialiqa-{index:04d}",
        "prompt": f"{context}\n\n{question}\n\n{choices}",
        "solution": f"{letter}. {answers[letter]}",
        "prompt_source_url": SOURCE_URL,
        "solution_source_url": SOURCE_URL,
    }


def main():
    rows = load_rows()
    if len(rows) != EXPECTED_COUNT:
        raise SystemExit(f"expected {EXPECTED_COUNT} rows, got {len(rows)}")
    tasks = [task(index, row) for index, row in enumerate(rows, start=1)]
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
