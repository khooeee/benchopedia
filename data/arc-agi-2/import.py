"""Import all 120 ARC-AGI-2 public evaluation tasks from their pinned GitHub commit.

Run from the repository root: python3 data/arc-agi-2/import.py
Only Python's standard library is required.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "arcprize/ARC-AGI-2"
EXPECTED_COUNT = 120
MAX_SIDE = 30


def fetch(revision, path):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{path}"
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8")


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
    if set(task) != {"train", "test"} or not train or not test:
        raise ValueError(f"{task_id}: expected train and test pairs")
    parts = [f"ARC-AGI-2 evaluation task {task_id}"]
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
        sys.exit("The declared scope must be all 120 public evaluation tasks.")
    task_ids = fetch(revision, "data/evaluation.txt").split()
    if (len(task_ids) != EXPECTED_COUNT or len(set(task_ids)) != EXPECTED_COUNT
            or not all(re.fullmatch(r"[0-9a-f]{8}", task_id) for task_id in task_ids)):
        sys.exit("The evaluation list must name 120 distinct eight-character task IDs.")
    tasks = [to_task(task_id, json.loads(fetch(revision, f"data/evaluation/{task_id}.json")), revision)
             for task_id in task_ids]
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
    print(f"Wrote {len(tasks):,} ARC-AGI-2 evaluation tasks to {out}")


if __name__ == "__main__":
    main()
