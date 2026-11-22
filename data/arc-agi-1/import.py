"""Import all 400 ARC-AGI-1 public evaluation tasks from their pinned GitHub commit.

Run from the repository root: python3 data/arc-agi-1/import.py
Only Python's standard library is required.
"""

import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "fchollet/ARC-AGI"
EXPECTED_COUNT = 400
MAX_SIDE = 30
TASK_FILE = re.compile(r"data/evaluation/([0-9a-f]{8})\.json")


def fetch(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read()


def evaluation_files(revision):
    """Map each evaluation task ID to its Git blob SHA in the commit's tree."""
    url = f"https://api.github.com/repos/{REPOSITORY}/git/trees/{revision}?recursive=1"
    tree = json.loads(fetch(url))
    if tree.get("truncated") or tree.get("sha") != revision:
        sys.exit("GitHub did not return the complete tree for the pinned commit.")
    files = {}
    for entry in tree["tree"]:
        path = entry["path"]
        if entry["type"] == "blob" and path.startswith("data/evaluation/"):
            match = TASK_FILE.fullmatch(path)
            if match is None:
                sys.exit(f"Unexpected evaluation file: {path}")
            files[match[1]] = entry["sha"]
    return files


def blob_sha(content):
    return hashlib.sha1(b"blob %d\0" % len(content) + content).hexdigest()


def render(grid, where):
    """Write a grid as one line of digits per row; each cell is a single digit."""
    if (not isinstance(grid, list) or not 1 <= len(grid) <= MAX_SIDE
            or not isinstance(grid[0], list) or not 1 <= len(grid[0]) <= MAX_SIDE):
        raise ValueError(f"{where}: grid must be 1 to 30 cells on each side")
    for row in grid:
        if (not isinstance(row, list) or len(row) != len(grid[0])
                or not all(type(cell) is int and 0 <= cell <= 9 for cell in row)):
            raise ValueError(f"{where}: grid rows must be equal lists of digits 0-9")
    size = f"{len(grid)}×{len(grid[0])}"
    return size, "\n".join("".join(map(str, row)) for row in grid)


def fenced(label, grid, where):
    size, rows = render(grid, where)
    return f"{label} ({size}):\n\n~~~\n{rows}\n~~~"


def to_task(task_id, task, revision):
    train, test = task.get("train"), task.get("test")
    # Files corrected in 2024 also repeat their ID in a "name" field.
    if set(task) - {"name"} != {"train", "test"} or task.get("name", task_id) != task_id:
        raise ValueError(f"{task_id}: expected train and test pairs")
    if not train or not test:
        raise ValueError(f"{task_id}: expected train and test pairs")
    parts = [f"ARC-AGI-1 evaluation task {task_id}"]
    for number, pair in enumerate(train, start=1):
        where = f"{task_id} example {number}"
        parts.append(f"## Example {number}\n\n" + fenced("Input", pair["input"], where)
                     + "\n\n" + fenced("Output", pair["output"], where))
    answers = []
    for number, pair in enumerate(test, start=1):
        where = f"{task_id} test {number}"
        parts.append(f"## Test input {number}\n\n" + fenced("Input", pair["input"], where))
        size, rows = render(pair["output"], where)
        answers.append(f"Test output {number} ({size}):\n{rows}")
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/data/evaluation/{task_id}.json"
    return {
        "key": task_id,
        "prompt": "\n\n".join(parts),
        "solution": "\n\n".join(answers),
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 400 public evaluation tasks.")
    files = evaluation_files(revision)
    if len(files) != EXPECTED_COUNT:
        sys.exit(f"Expected {EXPECTED_COUNT} evaluation task files, found {len(files)}.")
    tasks = []
    for task_id, expected_sha in sorted(files.items()):
        content = fetch(f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/data/evaluation/{task_id}.json")
        if blob_sha(content) != expected_sha:
            sys.exit(f"{task_id}: downloaded file does not match the pinned commit's blob.")
        tasks.append(to_task(task_id, json.loads(content), revision))
    tasks.sort(key=lambda task: task["key"])
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} ARC-AGI-1 evaluation tasks to {out}")


if __name__ == "__main__":
    main()
