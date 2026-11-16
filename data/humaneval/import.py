"""Import all 164 original HumanEval tasks from a pinned GitHub commit.

Run python3 data/humaneval/import.py from the repository root. Only Python's
standard library is required. Imported code is parsed, never executed.
"""

import ast
import gzip
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "openai/human-eval"
SOURCE_PATH = "data/HumanEval.jsonl.gz"
EXPECTED_COUNT = 164


def fetch_rows(revision):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{SOURCE_PATH}"
    with urllib.request.urlopen(url, timeout=60) as response:
        with gzip.GzipFile(fileobj=response) as compressed:
            # Iterate physical JSONL lines, preserving Unicode separators in text.
            with io.TextIOWrapper(compressed, encoding="utf-8") as stream:
                return [json.loads(line) for line in stream]


def to_task(row, revision):
    fields = ("task_id", "prompt", "canonical_solution", "test", "entry_point")
    if not isinstance(row, dict) or any(
            not isinstance(row.get(field), str) or not row[field].strip()
            for field in fields):
        raise ValueError("HumanEval requires an ID, prompt, solution, tests, and entry point")
    task_id, prompt, completion, tests, entry = (row[field] for field in fields)
    match = re.fullmatch(r"HumanEval/(0|[1-9][0-9]*)", task_id)
    if not match or not 0 <= int(match[1]) < EXPECTED_COUNT or not entry.isidentifier():
        raise ValueError(f"Invalid HumanEval task ID or entry point: {task_id}")
    # Match the authors' execution.py assembly, preserving every upstream field.
    solution = prompt + completion + "\n" + tests + "\n" + f"check({entry})"
    implementation = ast.parse(prompt + completion)
    test_tree = ast.parse(tests)
    if not any(isinstance(node, ast.FunctionDef) and node.name == entry
               for node in implementation.body):
        raise ValueError(f"{task_id}: entry point is absent from the implementation")
    if not any(isinstance(node, ast.FunctionDef) and node.name == "check"
               for node in test_tree.body):
        raise ValueError(f"{task_id}: missing check function")
    ast.parse(solution)
    fence = "`" * max(3, max((len(m[0]) for m in re.finditer(r"`+", prompt)), default=0) + 1)
    displayed = f"{task_id}: {entry}\n\n{fence}python\n{prompt}"
    if not prompt.endswith("\n"):
        displayed += "\n"
    displayed += fence
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{SOURCE_PATH}"
    return {
        "key": f"humaneval-{int(match[1]):03d}",
        "prompt": displayed,
        "solution": solution,
        "prompt_source_url": source,
        "solution_source_url": source,
        "environment_url": f"https://github.com/{REPOSITORY}/blob/{revision}/README.md#installation",
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must include all 164 original HumanEval tasks.")
    tasks = sorted((to_task(row, revision) for row in fetch_rows(revision)),
                   key=lambda task: task["key"])
    expected = {f"humaneval-{index:03d}" for index in range(EXPECTED_COUNT)}
    if len(tasks) != EXPECTED_COUNT or {task["key"] for task in tasks} != expected:
        sys.exit("HumanEval count or ID coverage differs from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} HumanEval tasks to {out}")


if __name__ == "__main__":
    main()
