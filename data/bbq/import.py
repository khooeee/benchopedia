"""Import all 58,492 BBQ examples from the authors' pinned GitHub commit.

Run from the repository root: python3 data/bbq/import.py
Only Python's standard library is required.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "nyu-mll/BBQ"
# Upstream category file and its expected example count.
CATEGORIES = {
    "Age": 3680,
    "Disability_status": 1556,
    "Gender_identity": 5672,
    "Nationality": 3080,
    "Physical_appearance": 1576,
    "Race_ethnicity": 6880,
    "Race_x_SES": 11160,
    "Race_x_gender": 15960,
    "Religion": 1200,
    "SES": 6864,
    "Sexual_orientation": 864,
}
EXPECTED_COUNT = sum(CATEGORIES.values())
LETTERS = "abc"
TEXT_FIELDS = ("context", "question", "ans0", "ans1", "ans2")


def source_path(category):
    return f"data/{category}.jsonl"


def fetch_examples(revision, category):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{source_path(category)}"
    with urllib.request.urlopen(url, timeout=120) as response:
        lines = response.read().decode("utf-8").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [json.loads(line) for line in lines]


def to_task(category, number, example, revision):
    where = f"{category} example {number}"
    if example.get("example_id") != number or example.get("category") != category:
        raise ValueError(f"{where}: unexpected example ID or category")
    for field in TEXT_FIELDS:
        text = example.get(field)
        if not isinstance(text, str) or not text.strip() or "\n" in text:
            raise ValueError(f"{where}: {field} must be one nonempty line")
    label = example.get("label")
    if label not in (0, 1, 2):
        raise ValueError(f"{where}: label must index one of three answers")
    options = [example[f"ans{index}"] for index in range(3)]
    lettered = "\n".join(f"({letter}) {option}" for letter, option in zip(LETTERS, options))
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{source_path(category)}"
    return {
        "key": f"{category.lower().replace('_', '-')}-{number:05d}",
        "prompt": f"{example['context']}\n\n{example['question']}\n\n{lettered}",
        "solution": f"({LETTERS[label]}) {options[label]}",
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 58,492 BBQ examples.")
    tasks = []
    for category, count in CATEGORIES.items():
        examples = fetch_examples(revision, category)
        if len(examples) != count:
            sys.exit(f"{category}: expected {count} examples, found {len(examples)}.")
        tasks.extend(to_task(category, number, example, revision)
                     for number, example in enumerate(examples))
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("BBQ count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} BBQ examples to {out}")


if __name__ == "__main__":
    main()
