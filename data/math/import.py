"""Import the complete MATH test split from its pinned Hugging Face revision.

Run from the repository root: python3 data/math/import.py
PyArrow is needed only to read the pinned Parquet files, not to build the site.
"""

import io
import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
DATASET = "EleutherAI/hendrycks_math"
# Subject file, expected test count, and the type label stored in every row.
SUBJECTS = {
    "algebra": (1187, "Algebra"),
    "counting_and_probability": (474, "Counting & Probability"),
    "geometry": (479, "Geometry"),
    "intermediate_algebra": (903, "Intermediate Algebra"),
    "number_theory": (540, "Number Theory"),
    "prealgebra": (871, "Prealgebra"),
    "precalculus": (546, "Precalculus"),
}
EXPECTED_COUNT = 5000
LEVELS = {f"Level {number}" for number in range(1, 6)}


def fetch_rows(revision, subject):
    try:
        import pyarrow.parquet as parquet
    except ImportError:
        sys.exit("This importer requires PyArrow. It is not used to build the site.")
    url = (f"https://huggingface.co/datasets/{DATASET}/resolve/{revision}/"
           f"{subject}/test-00000-of-00001.parquet")
    with urllib.request.urlopen(url, timeout=120) as response:
        payload = response.read()
    if not payload:
        raise ValueError(f"{subject}: empty test file")
    return parquet.read_table(io.BytesIO(payload)).to_pylist()


def final_answer(solution):
    """Return the last boxed or fboxed span, matching the authors' extractor."""
    start = solution.rfind("\\boxed")
    if start < 0:
        start = solution.rfind("\\fbox")
    if start < 0:
        return None
    depth = 0
    for index in range(start, len(solution)):
        if solution[index] == "{":
            depth += 1
        elif solution[index] == "}":
            depth -= 1
            if depth == 0:
                return solution[start:index + 1]
    return None


def to_task(subject, index, row):
    expected_count, expected_type = SUBJECTS[subject]
    problem, solution, level, kind = (row.get(field) for field in
                                       ("problem", "solution", "level", "type"))
    where = f"{subject} row {index}"
    if not isinstance(problem, str) or not problem.strip():
        raise ValueError(f"{where}: missing problem")
    if not isinstance(solution, str) or not solution.strip():
        raise ValueError(f"{where}: missing solution")
    if level not in LEVELS:
        raise ValueError(f"{where}: unexpected difficulty {level!r}")
    if kind != expected_type:
        raise ValueError(f"{where}: unexpected type {kind!r}")
    if final_answer(solution) is None:
        raise ValueError(f"{where}: solution has no boxed final answer")
    if not 0 <= index < expected_count:
        raise ValueError(f"{where}: row outside the declared subject count")
    source = (f"https://huggingface.co/datasets/{DATASET}/viewer/{subject}/test"
              f"?row={index}")
    return {
        "key": f"{subject}-test-{index + 1:04d}",
        "prompt": problem,
        "solution": solution,
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable Hugging Face commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be the complete 5,000-problem test split.")
    tasks = []
    for subject in sorted(SUBJECTS):
        rows = fetch_rows(revision, subject)
        if len(rows) != SUBJECTS[subject][0]:
            sys.exit(f"{subject}: expected {SUBJECTS[subject][0]} test rows, found {len(rows)}.")
        tasks.extend(to_task(subject, index, row) for index, row in enumerate(rows))
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("MATH count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    prompts = {}
    for task in tasks:
        prompts.setdefault(task["prompt"], []).append(task["key"])
    repeated = sum(len(keys) for keys in prompts.values() if len(keys) > 1)
    print(f"Wrote {len(tasks):,} MATH test tasks to {out}")
    print(f"Repeated problem texts: {repeated}")


if __name__ == "__main__":
    main()
