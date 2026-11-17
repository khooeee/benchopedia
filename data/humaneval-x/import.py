"""Import all 820 HumanEval-X problems from a pinned CodeGeeX commit.

Run from the repository root: python3 data/humaneval-x/import.py
Only Python's standard library is required. Imported code is never executed.
"""

import gzip
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "zai-org/CodeGeeX"
DATA_DIR = "codegeex/benchmark/humaneval-x"
PROBLEMS_PER_LANGUAGE = 164
# Upstream folder: task ID prefix, Benchopedia key prefix, and fence language.
LANGUAGES = {
    "python": ("Python", "python", "python"),
    "cpp": ("CPP", "cpp", "cpp"),
    "java": ("Java", "java", "java"),
    "js": ("JavaScript", "javascript", "javascript"),
    "go": ("Go", "go", "go"),
}
# Function definitions in each language's declaration; the last one is the task's function.
DEFINITIONS = {
    "python": r"^def (\w+)\(",
    "cpp": r"\b(\w+)\s*\([^()]*\)\s*\{",
    "java": r"public [^(=]*?\b(\w+)\s*\(",
    "js": r"^const (\w+) = ",
    "go": r"^func (\w+)\(",
}
KEYWORDS = {"for", "while", "if", "switch"}
EXPECTED_COUNT = len(LANGUAGES) * PROBLEMS_PER_LANGUAGE


def source_path(folder):
    return f"{DATA_DIR}/{folder}/data/humaneval_{folder}.jsonl.gz"


def fetch_rows(revision, folder):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{source_path(folder)}"
    with urllib.request.urlopen(url, timeout=60) as response:
        with gzip.GzipFile(fileobj=response) as compressed:
            # Iterate physical JSONL lines, preserving Unicode separators in text.
            with io.TextIOWrapper(compressed, encoding="utf-8") as stream:
                return [json.loads(line) for line in stream if line.strip()]


def function_name(folder, row):
    names = [name for name in re.findall(DEFINITIONS[folder], row["declaration"], re.M)
             if name not in KEYWORDS]
    if not names or names[-1] not in row["prompt"] or names[-1] not in row["test"]:
        raise ValueError(f"{row['task_id']}: cannot identify the function under test")
    return names[-1]


def to_task(folder, number, row, revision):
    prefix, key_prefix, fence_language = LANGUAGES[folder]
    task_id = f"{prefix}/{number}"
    if not isinstance(row, dict) or row.get("task_id") != task_id:
        raise ValueError(f"{folder} row {number}: expected task ID {task_id}")
    for field in ("prompt", "declaration", "canonical_solution", "test"):
        if not isinstance(row.get(field), str) or not row[field].strip():
            raise ValueError(f"{task_id}: missing {field}")
    prompt = row["prompt"]
    if "~~~" in prompt or not prompt.endswith("\n"):
        raise ValueError(f"{task_id}: prompt cannot be fenced intact")
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{source_path(folder)}"
    return {
        "key": f"{key_prefix}-{number:03d}",
        "prompt": f"{task_id}: {function_name(folder, row)}\n\n~~~{fence_language}\n{prompt}~~~",
        # The evaluation script runs prompt, completion, and tests in this order.
        "solution": prompt + row["canonical_solution"] + "\n" + row["test"],
        "prompt_source_url": source,
        "solution_source_url": source,
        "environment_url": (f"https://github.com/{REPOSITORY}/blob/{revision}/"
                            "codegeex/benchmark/README.md#evaluation-environment"),
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 820 HumanEval-X problems.")
    tasks = []
    for folder in LANGUAGES:
        rows = fetch_rows(revision, folder)
        if len(rows) != PROBLEMS_PER_LANGUAGE:
            sys.exit(f"{folder}: expected {PROBLEMS_PER_LANGUAGE} problems, found {len(rows)}.")
        tasks.extend(to_task(folder, number, row, revision) for number, row in enumerate(rows))
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("HumanEval-X count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} HumanEval-X problems to {out}")


if __name__ == "__main__":
    main()
