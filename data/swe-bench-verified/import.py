"""Snapshot SWE-bench Verified's tasks into data/swe-bench-verified/tasks.jsonl.

Refuses to run if the upstream dataset is no longer at the revision pinned in
benchmark.json, so picking up an upstream change is always a deliberate edit.
"""

import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

DATASET = "princeton-nlp/SWE-bench_Verified"
PAGE_SIZE = 100
# Pin the readable environment recipes independently of the dataset snapshot.
TASK_REPO_REVISION = "3d07b464b7b311a0cbfb5ed5b2d8a3b96f84a33d"

BENCHMARK_DIR = Path(__file__).resolve().parent


def get_json(url):
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def upstream_revision():
    return get_json(f"https://huggingface.co/api/datasets/{DATASET}")["sha"]


def fetch_rows():
    rows = []
    total = None
    while total is None or len(rows) < total:
        query = urllib.parse.urlencode(
            {
                "dataset": DATASET,
                "config": "default",
                "split": "test",
                "offset": len(rows),
                "length": PAGE_SIZE,
            }
        )
        page = get_json(f"https://datasets-server.huggingface.co/rows?{query}")
        for item in page["rows"]:
            if {"patch", "problem_statement"}.intersection(item.get("truncated_cells", [])):
                sys.exit("Upstream returned a truncated prompt or reference patch; import cancelled.")
        if not page["rows"]:
            break
        total = page["num_rows_total"]
        rows.extend(item["row"] for item in page["rows"])
    return rows


def to_task(row):
    # Instance ids are "<owner>__<repo>-<pull request number>".
    pull_number = row["instance_id"].rsplit("-", 1)[1]
    pull_url = f"https://github.com/{row['repo']}/pull/{pull_number}"
    solution = row["patch"]
    if not isinstance(solution, str) or not solution.strip():
        raise ValueError(f"{row['instance_id']}: missing reference patch")
    return {
        "key": row["instance_id"],
        "prompt": row["problem_statement"],
        "solution": solution,
        "environment_url": f"https://github.com/SWE-bench/swe-bench-tasks/blob/{TASK_REPO_REVISION}/tasks/{row['instance_id']}/Dockerfile",
        "solution_source_url": f"{pull_url}/files",
        "prompt_source_url": pull_url,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text())
    pinned = benchmark["dataset_revision"]
    before = upstream_revision()
    if before != pinned:
        sys.exit(
            f"{DATASET} is at {before} but benchmark.json pins {pinned}.\n"
            "Update dataset_revision in benchmark.json to import the new revision."
        )

    tasks = sorted((to_task(row) for row in fetch_rows()), key=lambda q: q["key"])
    if len(tasks) != benchmark["task_count"] or len({task["key"] for task in tasks}) != len(tasks):
        sys.exit("Upstream task count or identifiers do not match the benchmark; import cancelled.")

    if upstream_revision() != before:
        sys.exit(f"{DATASET} changed during the import; run it again.")

    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as f:
        for task in tasks:
            f.write(json.dumps(task, ensure_ascii=False) + "\n")
    temporary.replace(out)
    print(f"Wrote {len(tasks)} tasks to {out}")


if __name__ == "__main__":
    main()
