"""Import every official IFEval prompt from the pinned Google Research commit.

Run from the repository root: python3 data/ifeval/import.py
Only Python's standard library is required. Updating the source intentionally
requires updating both dataset_revision and SOURCE_SHA256.
"""

import hashlib
import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "google-research/google-research"
SOURCE_PATH = "instruction_following_eval/data/input_data.jsonl"
SOURCE_SHA256 = "67ffeee0fcb87c317c5b08a2de85557b4a7e96ada6178aa645b4954fe4b53d49"
EXPECTED_COUNT = 541


def fetch_rows(revision):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{SOURCE_PATH}"
    with urllib.request.urlopen(url, timeout=60) as response:
        content = response.read()
    if hashlib.sha256(content).hexdigest() != SOURCE_SHA256:
        raise ValueError("IFEval source checksum differs from the verified snapshot")
    # Iterate physical lines, preserving Unicode separators inside prompt text.
    with io.TextIOWrapper(io.BytesIO(content), encoding="utf-8") as stream:
        return [json.loads(line) for line in stream]


def to_task(row, line, revision):
    if not isinstance(row, dict):
        raise ValueError(f"Line {line}: expected a task object")
    key, prompt = row.get("key"), row.get("prompt")
    if type(key) is not int or key < 0:
        raise ValueError(f"Line {line}: missing or invalid upstream key")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError(f"Line {line}: missing prompt")
    instructions, kwargs = row.get("instruction_id_list"), row.get("kwargs")
    if (not isinstance(instructions, list) or not instructions
            or any(not isinstance(value, str) or not value.strip()
                   for value in instructions)):
        raise ValueError(f"Line {line}: missing instruction IDs")
    if (not isinstance(kwargs, list) or len(kwargs) != len(instructions)
            or any(not isinstance(value, dict) for value in kwargs)):
        raise ValueError(f"Line {line}: missing or mismatched grading parameters")
    base = f"https://github.com/{REPOSITORY}/blob/{revision}"
    return {
        "key": str(key),
        "prompt": prompt,
        "prompt_source_url": f"{base}/{SOURCE_PATH}#L{line}",
        "environment_url": f"{base}/instruction_following_eval/README.md#how-to-run",
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be the complete 541-prompt IFEval dataset.")
    tasks = [to_task(row, line, revision)
             for line, row in enumerate(fetch_rows(revision), start=1)]
    tasks.sort(key=lambda task: int(task["key"]))
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("IFEval count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} IFEval tasks to {out}")


if __name__ == "__main__":
    main()
