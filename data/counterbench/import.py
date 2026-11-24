"""Import both complete question files from the authors' CounterBench release."""

from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
DATASET = "CounterBench/CounterBench"
FILES = (
    (
        "alpha",
        "data_balanced_alpha_V1.json",
        "39f935a48fb997869c1e4488c9a2b902dc08acd876da557c675722c269391a76",
        {"basic": 250, "conditional": 250, "joint": 250, "nested": 250},
    ),
    (
        "backdoor",
        "data_balanced_backdoor_V2.json",
        "e04eb6e58508ef3d6c40051a8f8976dff9486dea3190e5a47418d3bca5ef1771",
        {"backdoor": 200},
    ),
)


def load_tasks(revision, group, name, expected_digest, expected_counts):
    dataset = f"https://huggingface.co/datasets/{DATASET}"
    with urlopen(f"{dataset}/resolve/{revision}/{name}", timeout=60) as response:
        payload = response.read()
    if sha256(payload).hexdigest() != expected_digest:
        raise ValueError(f"{name} does not match its pinned SHA-256")
    records = json.loads(payload)
    if not isinstance(records, list):
        raise ValueError(f"Expected a list of records in {name}")

    counts = Counter()
    tasks = []
    source = f"{dataset}/blob/{revision}/{name}"
    for index, record in enumerate(records, 1):
        context = record["given_info"]
        question = record["question"]
        answer = record["answer"]
        case = record["type"]
        upstream_id = record["question_id"]
        if (not isinstance(upstream_id, str) or not re.fullmatch(r"0|[1-9][0-9]{0,2}", upstream_id)
                or any(not isinstance(value, str) or not value.strip() for value in (context, question))
                or answer not in ("yes", "no") or case not in expected_counts):
            raise ValueError(f"Invalid {name} record at position {index}")
        counts[case] += 1
        tasks.append({
            "key": f"counterbench-{group}-{int(upstream_id):03d}",
            "prompt": context + "\n\n" + question,
            "solution": answer,
            "prompt_source_url": source,
            "solution_source_url": source,
        })
    if counts != expected_counts:
        raise ValueError(f"Unexpected question counts in {name}: {counts}")
    return tasks


def main():
    metadata = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = metadata["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must be an immutable Hugging Face Git commit")
    tasks = [task for file in FILES for task in load_tasks(revision, *file)]
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != metadata["task_count"] or len({task["key"] for task in tasks}) != len(tasks):
        raise ValueError("CounterBench count or identifiers differ from the declared scope")

    with NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False
    ) as temporary:
        path = Path(temporary.name)
        try:
            for task in tasks:
                temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
            temporary.close()
            path.replace(HERE / "tasks.jsonl")
        finally:
            path.unlink(missing_ok=True)
    print(f"Imported {len(tasks):,} CounterBench questions.")


if __name__ == "__main__":
    main()
