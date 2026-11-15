"""Snapshot SWE-bench Verified's questions into data/swe-bench-verified/questions.jsonl.

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

BENCHMARK_DIR = Path(__file__).resolve().parent.parent / "data" / "swe-bench-verified"


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
        if not page["rows"]:
            break
        total = page["num_rows_total"]
        rows.extend(item["row"] for item in page["rows"])
    return rows


def to_question(row):
    # Instance ids are "<owner>__<repo>-<pull request number>".
    pull_number = row["instance_id"].rsplit("-", 1)[1]
    return {
        "key": row["instance_id"],
        "prompt": row["problem_statement"],
        "source_url": f"https://github.com/{row['repo']}/pull/{pull_number}",
        "attrs": {
            "repo": row["repo"],
            "base_commit": row["base_commit"],
            "version": row["version"],
            "created_at": row["created_at"],
            "difficulty": row["difficulty"],
            "fail_to_pass": json.loads(row["FAIL_TO_PASS"]),
            "pass_to_pass_count": len(json.loads(row["PASS_TO_PASS"])),
        },
    }


def main():
    pinned = json.loads((BENCHMARK_DIR / "benchmark.json").read_text())["dataset_revision"]
    before = upstream_revision()
    if before != pinned:
        sys.exit(
            f"{DATASET} is at {before} but benchmark.json pins {pinned}.\n"
            "Update dataset_revision in benchmark.json to import the new revision."
        )

    questions = sorted((to_question(row) for row in fetch_rows()), key=lambda q: q["key"])

    if upstream_revision() != before:
        sys.exit(f"{DATASET} changed during the import; run it again.")

    out = BENCHMARK_DIR / "questions.jsonl"
    with out.open("w", encoding="utf-8", newline="\n") as f:
        for question in questions:
            f.write(json.dumps(question, ensure_ascii=False) + "\n")
    print(f"Wrote {len(questions)} questions to {out}")


if __name__ == "__main__":
    main()
