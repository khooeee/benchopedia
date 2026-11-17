"""Import all 800 CRUXEval samples from their pinned GitHub commit.

Run from the repository root: python3 data/cruxeval/import.py
Only Python's standard library is required.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "facebookresearch/cruxeval"
SOURCE_PATH = "data/cruxeval.jsonl"
FIELDS = {"id", "code", "input", "output"}
EXPECTED_COUNT = 800


def fetch_samples(revision):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{SOURCE_PATH}"
    with urllib.request.urlopen(url, timeout=120) as response:
        lines = response.read().decode("utf-8").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [json.loads(line) for line in lines]


def to_task(line, sample, revision):
    number = line - 1
    if set(sample) != FIELDS or sample["id"] != f"sample_{number}":
        raise ValueError(f"Line {line}: expected sample_{number} with code, input, and output")
    for field in ("code", "input", "output"):
        if not isinstance(sample[field], str):
            raise ValueError(f"{sample['id']}: missing {field}")
    code, given_input, output = sample["code"], sample["input"], sample["output"]
    # sample_135's function takes no arguments, so only its input is empty.
    if not code.strip() or not output.strip() or not given_input.strip() and number != 135:
        raise ValueError(f"{sample['id']}: missing code, input, or output")
    if "\n" in given_input or "\n" in output:
        raise ValueError(f"{sample['id']}: input and output must each fit on one line")
    if "def f(" not in code or re.search(r"^\s*~{3,}", code, re.M):
        raise ValueError(f"{sample['id']}: expected a function f outside tilde fences")
    # The two assertions the authors' prompts show inside [PYTHON] blocks.
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{SOURCE_PATH}?plain=1#L{line}"
    return {
        "key": f"sample-{number:03d}",
        "prompt": (f"{sample['id']}\n\n## Output prediction (CRUXEval-O)\n\n"
                   f"~~~python\n{code}\nassert f({given_input}) == ??\n~~~\n\n"
                   f"## Input prediction (CRUXEval-I)\n\n"
                   f"~~~python\n{code}\nassert f(??) == {output}\n~~~"),
        "solution": f"assert f({given_input}) == {output}",
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 800 CRUXEval samples.")
    samples = fetch_samples(revision)
    if len(samples) != EXPECTED_COUNT:
        sys.exit(f"Expected {EXPECTED_COUNT} samples, found {len(samples)}.")
    tasks = [to_task(line, sample, revision) for line, sample in enumerate(samples, start=1)]
    tasks.sort(key=lambda task: task["key"])
    if len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("CRUXEval identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} CRUXEval samples to {out}")


if __name__ == "__main__":
    main()
