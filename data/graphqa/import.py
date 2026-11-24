"""Import GraphQA's seven complete basic zero-shot test splits."""

from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
DATASET = "baharef/GraphQA"
SPLITS = {
    "connected_nodes": "731b957caf3ea568b433e05b8a1513dade213921e1d884e3a13294680a20eef3",
    "cycle_check": "541628a5f7ac0dd7bce7b66edb810901df3f03b153c59c59ec6ce1613db25b9e",
    "disconnected_nodes": "770ccd7464e854a374e3d28fdc0bc5a53b02e3f9b8aa498688ebdc8cbc5f7036",
    "edge_count": "09a5678abb49a2bd574864f0fc3da7b52410becbd5cee7bf75fca8e8f578362a",
    "edge_existence": "30d9974639b676580c1ae7df84f53d5d444a992dc5b0d2e7c90909b74647139d",
    "node_count": "6da7bbc5e9a8b3ae176005c6545f4a690568fe2341ff4af54c4e2b001bd7e342",
    "node_degree": "12a050d858fbfb0cf1de78b9be4a603d2b13d921c25924680382a7cf50bf2fb6",
}


def load_tasks(revision, config, digest):
    dataset = f"https://huggingface.co/datasets/{DATASET}"
    file = f"{config}/{config}_zero_shot_test.json"
    with urlopen(f"{dataset}/resolve/{revision}/{file}", timeout=60) as response:
        payload = response.read()
    if sha256(payload).hexdigest() != digest:
        raise ValueError(f"{file} does not match its pinned SHA-256")
    records = json.loads(payload)
    if not isinstance(records, list) or len(records) != 500:
        raise ValueError(f"{file} must contain 500 records")

    source = f"{dataset}/blob/{revision}/{file}"
    slug = config.replace("_", "-")
    tasks = []
    for number, record in enumerate(records, 1):
        question, answer = record["question"], record["answer"]
        if (not isinstance(question, str) or not question.strip()
                or not isinstance(answer, str) or not answer.strip()
                or record["algorithm"] != "er" or record["text_encoding"] != "adjacency"):
            raise ValueError(f"{file} has an invalid record at row {number}")
        tasks.append({
            "key": f"graphqa-{slug}-{number:03d}",
            "prompt": question,
            "solution": answer,
            "prompt_source_url": source,
            "solution_source_url": source,
        })
    return tasks


def main():
    benchmark = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must be an immutable Hugging Face Git commit")
    tasks = [task for config, digest in SPLITS.items() for task in load_tasks(revision, config, digest)]
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != benchmark["task_count"] or len({task["key"] for task in tasks}) != len(tasks):
        raise ValueError("GraphQA count or identifiers differ from the declared scope")

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
    print(f"Imported {len(tasks):,} GraphQA basic zero-shot test questions.")


if __name__ == "__main__":
    main()
