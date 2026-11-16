"""Import the complete original GSM8K test split from its pinned GitHub commit.

Run from the repository root: python3 data/gsm8k/import.py
Only Python's standard library is required.
"""

import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "openai/grade-school-math"
SOURCE_PATH = "grade_school_math/data/test.jsonl"
EXPECTED_COUNT = 1319


def fetch_rows(revision):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{SOURCE_PATH}"
    with urllib.request.urlopen(url, timeout=60) as response:
        # Iterate physical lines; Unicode line separators can occur inside text.
        with io.TextIOWrapper(response, encoding="utf-8") as stream:
            return [json.loads(line) for line in stream]


def to_task(row, line, revision):
    if not isinstance(row, dict):
        raise ValueError(f"Line {line}: expected a problem object")
    question, answer = row.get("question"), row.get("answer")
    if not isinstance(question, str) or not question.strip():
        raise ValueError(f"Line {line}: missing question")
    if (not isinstance(answer, str)
            or not re.fullmatch(r"[\s\S]+\n#### -?[0-9][0-9.,]*", answer)):
        raise ValueError(f"Line {line}: missing worked solution or final numeric answer")
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{SOURCE_PATH}#L{line}"
    return {
        "key": f"test-{line:04d}",
        "prompt": question,
        "solution": answer,
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be the complete 1,319-problem test split.")
    tasks = [to_task(row, line, revision)
             for line, row in enumerate(fetch_rows(revision), start=1)]
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("GSM8K count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} GSM8K test tasks to {out}")


if __name__ == "__main__":
    main()
