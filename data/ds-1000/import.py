"""Import all 1,000 DS-1000 problems from their pinned Hugging Face revision.

Run from the repository root: python3 data/ds-1000/import.py
Only Python's standard library is required.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "xlangai/DS-1000"
DATA_PATH = "test.jsonl"
# The GitHub commit whose environment.yml defines the official test environment.
CODE_REPOSITORY = "xlang-ai/DS-1000"
CODE_REVISION = "b39aab71da6d23ef8d3cac59a7c5f834516ab334"
# Library and its expected problem count.
LIBRARIES = {
    "Pandas": 291,
    "Numpy": 220,
    "Matplotlib": 155,
    "Tensorflow": 45,
    "Scipy": 106,
    "Sklearn": 115,
    "Pytorch": 68,
}
EXPECTED_COUNT = sum(LIBRARIES.values())
PERTURBATIONS = {"Origin", "Surface", "Semantic", "Difficult-Rewrite"}
METADATA_FIELDS = {"problem_id", "library_problem_id", "library", "test_case_cnt",
                   "perturbation_type", "perturbation_origin_id"}


def fetch_problems(revision):
    url = f"https://huggingface.co/datasets/{REPOSITORY}/resolve/{revision}/{DATA_PATH}"
    with urllib.request.urlopen(url, timeout=120) as response:
        lines = response.read().decode("utf-8").split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    return [json.loads(line) for line in lines]


def heading(metadata):
    library, number = metadata["library"], metadata["library_problem_id"]
    kind = metadata["perturbation_type"]
    if kind == "Origin":
        return f"{library} problem {number}, Origin"
    return f"{library} problem {number}, {kind} perturbation of problem {metadata['perturbation_origin_id']}"


def to_task(number, record, revision):
    where = f"problem {number}"
    if set(record) != {"prompt", "reference_code", "metadata", "code_context"}:
        raise ValueError(f"{where}: unexpected fields")
    metadata = record["metadata"]
    if set(metadata) != METADATA_FIELDS or metadata["problem_id"] != number:
        raise ValueError(f"{where}: problem IDs must run from 0 in file order")
    if metadata["library"] not in LIBRARIES or metadata["perturbation_type"] not in PERTURBATIONS:
        raise ValueError(f"{where}: unknown library or perturbation type")
    for field in ("prompt", "reference_code", "code_context"):
        text = record[field]
        if not isinstance(text, str) or not text.strip():
            raise ValueError(f"{where}: missing {field}")
    # The prompt mixes prose and Python; a tilde fence keeps its text and indentation intact.
    if "~~~" in record["prompt"]:
        raise ValueError(f"{where}: prompt contains a tilde fence")
    source = f"https://huggingface.co/datasets/{REPOSITORY}/blob/{revision}/{DATA_PATH}"
    return {
        "key": f"problem-{number:03d}",
        "prompt": f"{heading(metadata)}\n\n~~~text\n{record['prompt']}\n~~~",
        "solution": record["reference_code"],
        "prompt_source_url": source,
        "solution_source_url": source,
        "environment_url": (f"https://github.com/{CODE_REPOSITORY}/blob/{CODE_REVISION}/"
                            "environment.yml"),
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable Hugging Face commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 1,000 DS-1000 problems.")
    records = fetch_problems(revision)
    if len(records) != EXPECTED_COUNT:
        sys.exit(f"Expected {EXPECTED_COUNT} problems in {DATA_PATH}, found {len(records)}.")
    tasks = [to_task(number, record, revision) for number, record in enumerate(records)]
    for library, count in LIBRARIES.items():
        numbers = sorted(record["metadata"]["library_problem_id"] for record in records
                         if record["metadata"]["library"] == library)
        if numbers != list(range(count)):
            sys.exit(f"{library}: expected problems 0 to {count - 1}.")
    tasks.sort(key=lambda task: task["key"])
    if len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("DS-1000 identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} DS-1000 problems to {out}")


if __name__ == "__main__":
    main()
