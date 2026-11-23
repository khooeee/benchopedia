"""Import the complete original ListOps test split at a pinned Git revision."""

import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
REPOSITORY = "NYU-MLL/spinn"
UPSTREAM_FILE = "python/spinn/data/listops/test_d20s.tsv"
INTRO = (
    "Evaluate this ListOps expression. MIN and MAX take the smallest or largest value. "
    "MED takes the median and rounds down. SM sums the values modulo 10. "
    "Evaluate the inner lists before using their results in the enclosing lists."
)
DIGITS = set("0123456789")
TOKENS = DIGITS | {"[MIN", "[MAX", "[MED", "[SM", "]"}


def parse_test_file(payload, revision):
    rows = []
    for number, line in enumerate(payload.splitlines(), 1):
        label, separator, expression = line.partition("\t")
        if not separator or label not in DIGITS:
            raise ValueError(f"Invalid ListOps label or separator at line {number}")
        leaves = [token for token in expression.split(" ") if token not in {"(", ")"}]
        if not leaves or any(token not in TOKENS for token in leaves):
            raise ValueError(f"Invalid ListOps expression at line {number}")
        rows.append({
            "key": f"listops-{number:05d}",
            "prompt": INTRO + "\n\n" + " ".join(leaves),
            "solution": label,
            "prompt_source_url": f"https://github.com/{REPOSITORY}/blob/{revision}/{UPSTREAM_FILE}#L{number}",
        })
    return rows


def main():
    metadata = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = metadata["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must be a full Git commit")
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{UPSTREAM_FILE}"
    with urlopen(url, timeout=60) as response:
        rows = parse_test_file(response.read().decode("utf-8"), revision)
    if len(rows) != metadata["task_count"]:
        raise ValueError(f"Expected {metadata['task_count']} ListOps rows, got {len(rows)}")

    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=HERE, delete=False) as temporary:
        path = Path(temporary.name)
        try:
            for row in rows:
                temporary.write(json.dumps(row, ensure_ascii=False) + "\n")
            temporary.close()
            path.replace(HERE / "tasks.jsonl")
        finally:
            path.unlink(missing_ok=True)
    print(f"Imported {len(rows):,} ListOps test expressions.")


if __name__ == "__main__":
    main()
