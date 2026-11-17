"""Import all 3,600 NATURAL PLAN test examples from their pinned GitHub commit.

Run from the repository root: python3 data/natural-plan/import.py
Only Python's standard library is required.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "google-deepmind/natural-plan"
# Upstream task name and its expected example count.
TASKS = {
    "trip_planning": 1600,
    "meeting_planning": 1000,
    "calendar_scheduling": 1000,
}
EXPECTED_COUNT = sum(TASKS.values())


def source_path(task_name):
    return f"data/{task_name}.json"


def fetch_examples(revision, task_name):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{source_path(task_name)}"
    with urllib.request.urlopen(url, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def golden_text(example_id, plan):
    # Meeting-planning plans are lists of steps; the other tasks store one string.
    if isinstance(plan, list):
        if not plan or not all(isinstance(step, str) and step.strip() and "\n" not in step
                               for step in plan):
            raise ValueError(f"{example_id}: plan steps must be nonempty single lines")
        return "\n".join(plan)
    if not isinstance(plan, str) or not plan.strip():
        raise ValueError(f"{example_id}: missing golden plan")
    return plan


def to_task(task_name, number, example, revision):
    example_id = f"{task_name}_example_{number}"
    prompt = example.get("prompt_0shot")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError(f"{example_id}: missing zero-shot prompt")
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{source_path(task_name)}"
    return {
        "key": f"{task_name.replace('_', '-')}-{number:04d}",
        "prompt": f"{example_id}\n\n{prompt}",
        "solution": golden_text(example_id, example.get("golden_plan")),
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 3,600 NATURAL PLAN test examples.")
    tasks = []
    for task_name, count in TASKS.items():
        examples = fetch_examples(revision, task_name)
        if sorted(examples) != sorted(f"{task_name}_example_{number}" for number in range(count)):
            sys.exit(f"{task_name}: expected examples 0 to {count - 1}.")
        tasks.extend(to_task(task_name, number, examples[f"{task_name}_example_{number}"], revision)
                     for number in range(count))
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("NATURAL PLAN count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} NATURAL PLAN examples to {out}")


if __name__ == "__main__":
    main()
