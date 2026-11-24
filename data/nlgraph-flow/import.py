#!/usr/bin/env python3
"""Import the complete easy and hard NLGraph standard maximum-flow tests."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
REPOSITORY = "Arthur-Heng/NLGraph"
DIRECTORY = "NLGraph/flow/graph"
GROUPS = {
    "easy": (150, "fd10db4fa9acfc63f5d8eff76f065a1b5d1026814aabcc5b1c4b2c190ed7cbec"),
    "hard": (200, "2af7fd369b476add0525c930ec1e3a9b82ee2ad13e54b50d071a637863f2cc31"),
}


def download(url):
    with urlopen(url, timeout=30) as response:
        return response.read()


def payloads(raw, difficulty, count, local_dir):
    filenames = [f"graph{i}.txt" for i in range(count)]
    if local_dir is not None:
        return [(local_dir / difficulty / name).read_bytes() for name in filenames]
    urls = [f"{raw}/{difficulty}/standard/{name}" for name in filenames]
    with ThreadPoolExecutor(max_workers=12) as executor:
        return list(executor.map(download, urls))


def parse_graph(payload, key, source_url):
    lines = [tuple(map(int, line.split())) for line in payload.decode("utf-8").splitlines()]
    vertices, edge_count = lines[0]
    source, sink = lines[-2]
    (flow,) = lines[-1]
    edges = lines[1:-2]
    if (vertices < 2 or not edges or len(edges) != edge_count or source == sink
            or not (0 <= source < vertices and 0 <= sink < vertices) or flow < 0
            or any(len(edge) != 3 for edge in edges)):
        raise ValueError(f"{key}: invalid graph header, query or target")
    if (len({(u, v) for u, v, _ in edges}) != edge_count
            or any(u == v or not (0 <= u < vertices and 0 <= v < vertices and capacity > 0)
                   for u, v, capacity in edges)):
        raise ValueError(f"{key}: invalid directed capacity edges")

    # The official formatter iterates nodes in ascending order and keeps
    # each node's edges in insertion order.
    ordered = sorted(edges, key=lambda edge: edge[0])
    edge_lines = [f"an edge from node {u} to node {v} with capacity {c}" for u, v, c in ordered]
    prompt = (
        f"In a directed graph, the nodes are numbered from 0 to {vertices - 1}, and the edges are:\n"
        + ",\n".join(edge_lines) + ".\n"
        f"Q: What is the maximum flow from node {source} to node {sink}?\nA:"
    )
    return {
        "key": key,
        "prompt": prompt,
        "solution": str(flow),
        "prompt_source_url": source_url,
        "solution_source_url": source_url,
    }


def load_tasks(local_dir=None):
    metadata = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = metadata["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must identify an immutable Git commit")
    raw = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{DIRECTORY}"
    web = f"https://github.com/{REPOSITORY}/blob/{revision}/{DIRECTORY}"
    tasks = []
    for difficulty, (count, checksum) in GROUPS.items():
        records = payloads(raw, difficulty, count, local_dir)
        if sha256(b"".join(records)).hexdigest() != checksum:
            raise ValueError(f"{difficulty}: source files differ from the reviewed snapshot")
        for index, record in enumerate(records):
            source = f"{web}/{difficulty}/standard/graph{index}.txt"
            tasks.append(parse_graph(record, f"{difficulty}-{index:03d}", source))
    if len(tasks) != metadata["task_count"]:
        raise ValueError("Imported task count differs from benchmark.json")
    return tasks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-dir", type=Path, help="Use local easy and hard directories with the pinned files")
    args = parser.parse_args()
    tasks = load_tasks(args.local_dir)
    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False) as temporary:
        for task in tasks:
            temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
    Path(temporary.name).replace(HERE / "tasks.jsonl")
    print(f"Imported {len(tasks):,} NLGraph maximum-flow tasks")


if __name__ == "__main__":
    main()
