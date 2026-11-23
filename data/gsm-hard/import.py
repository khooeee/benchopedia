"""Import every GSM-Hard example from the pinned authors' JSONL release."""

from decimal import Decimal
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
DATASET = "reasoning-machines/gsm-hard"
FILENAME = "gsmhardv2.jsonl"


def load_rows(payload, revision):
    rows = []
    source = f"https://huggingface.co/datasets/{DATASET}/blob/{revision}/{FILENAME}"
    for number, line in enumerate(payload, 1):
        row = json.loads(line, parse_float=Decimal)
        value = row["target"]
        question = row["input"]
        if not isinstance(question, str) or not question.strip():
            raise ValueError(f"Invalid problem at line {number}")
        if type(value) not in (int, Decimal) or not Decimal(value).is_finite():
            raise ValueError(f"Invalid numeric target at line {number}")
        rows.append({
            "key": f"gsm-hard-{number:04d}",
            "prompt": question,
            "solution": format(value, "f") if type(value) is Decimal else str(value),
            "prompt_source_url": source,
        })
    return rows


def main():
    metadata = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = metadata["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must be an immutable Hugging Face Git commit")
    url = f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/{FILENAME}"
    with urlopen(url, timeout=60) as response:
        rows = load_rows(response, revision)
    if len(rows) != metadata["task_count"]:
        raise ValueError(f"Expected {metadata['task_count']} test rows, got {len(rows)}")

    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=HERE, delete=False) as temporary:
        path = Path(temporary.name)
        try:
            for row in rows:
                temporary.write(json.dumps(row, ensure_ascii=False) + "\n")
            temporary.close()
            path.replace(HERE / "tasks.jsonl")
        finally:
            path.unlink(missing_ok=True)
    print(f"Imported {len(rows):,} GSM-Hard problems.")


if __name__ == "__main__":
    main()
