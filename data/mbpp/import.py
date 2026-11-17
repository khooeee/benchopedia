"""Import the official MBPP test split, task IDs 11 through 510.

Run from the repository root: python3 data/mbpp/import.py
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
SOURCE_PATH = "mbpp/mbpp.jsonl"
SOURCE_SHA256 = "ccf64ceae9c5403bf50a044cb6d505bfd2a2963ee58338ba268fd65beab92a9f"
EXPECTED_IDS = set(range(11, 511))


def fetch_rows(revision):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{SOURCE_PATH}"
    with urllib.request.urlopen(url, timeout=60) as response:
        content = response.read()
    if hashlib.sha256(content).hexdigest() != SOURCE_SHA256:
        raise ValueError("MBPP source checksum differs from the verified snapshot")
    rows = []
    with io.TextIOWrapper(io.BytesIO(content), encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            row = json.loads(line)
            row["_line"] = line_number
            rows.append(row)
    return rows


def normalize_newlines(text):
    """The published pages round-trip line feeds, not the upstream CR LF."""
    return text.replace("\r\n", "\n").replace("\r", "\n")


def fence(text):
    width = max((len(match.group(0)) for match in re.finditer(r"`+", text)), default=0)
    marker = "`" * max(3, width + 1)
    body = text if text.endswith("\n") else text + "\n"
    return f"{marker}python\n{body}{marker}"


def to_prompt(row):
    parts = [row["text"]]
    setup = normalize_newlines(row["test_setup_code"])
    if setup.strip():
        parts.append("Test setup:\n\n" + fence(setup))
    parts.append("Your code should pass these tests:\n\n" + fence("\n".join(row["test_list"])))
    if row["challenge_test_list"]:
        parts.append("Additional tests:\n\n" + fence("\n".join(row["challenge_test_list"])))
    return "\n\n".join(parts)


def to_task(row, revision):
    task_id = row.get("task_id")
    text, code = row.get("text"), row.get("code")
    tests, extra, setup = (row.get("test_list"), row.get("challenge_test_list"),
                            row.get("test_setup_code"))
    if type(task_id) is not int or task_id not in EXPECTED_IDS:
        raise ValueError(f"Unexpected task ID: {task_id!r}")
    if not isinstance(text, str) or not text.strip() or "\n" in text or "\r" in text:
        raise ValueError(f"Task {task_id}: missing single-line problem text")
    if not isinstance(code, str) or not code.strip():
        raise ValueError(f"Task {task_id}: missing reference solution")
    if not isinstance(setup, str):
        raise ValueError(f"Task {task_id}: missing test setup field")
    if (not isinstance(tests, list) or len(tests) != 3
            or any(not isinstance(test, str) or not test.startswith("assert ") for test in tests)):
        raise ValueError(f"Task {task_id}: expected three assert tests")
    if (not isinstance(extra, list)
            or any(not isinstance(test, str) or not test.startswith("assert ") for test in extra)):
        raise ValueError(f"Task {task_id}: invalid additional tests")
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{SOURCE_PATH}#L{row['_line']}"
    return {
        "key": f"mbpp-{task_id:04d}",
        "prompt": to_prompt(row),
        "solution": normalize_newlines(code),
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != len(EXPECTED_IDS):
        sys.exit("The declared scope must be the 500-problem test split.")
    selected = [row for row in fetch_rows(revision) if row.get("task_id") in EXPECTED_IDS]
    tasks = sorted((to_task(row, revision) for row in selected), key=lambda task: task["key"])
    found = {int(task["key"].removeprefix("mbpp-")) for task in tasks}
    if len(tasks) != len(EXPECTED_IDS) or found != EXPECTED_IDS:
        sys.exit("MBPP count or task IDs differ from the declared test split.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} MBPP test tasks to {out}")


if __name__ == "__main__":
    main()
