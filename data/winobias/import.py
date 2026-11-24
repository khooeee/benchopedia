#!/usr/bin/env python3
"""Import all four test files from the pinned WinoBias CoNLL release."""

import argparse
from collections import defaultdict
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from eval import numbered_tokens, parse_clusters


HERE = Path(__file__).resolve().parent
DIRECTORY = "WinoBias/wino/data/conll_format"
PARTS = {
    "type1-anti": "68a7f4f0f055f5cddeed3b0a07a572fded2b2077c1afd2bb596c02e5fe0c9476",
    "type1-pro": "419c0f4ecff4c6b1d81f0ce646e8ce1ebff9bde4729295064049ed9f97ad25d1",
    "type2-anti": "c9a6b66d60ce6a008f0d8cb619786042454abc6e9502d134cf88352aed7da57b",
    "type2-pro": "7720dee1432dc6a3d6077c442ddea37c63773e80f4f75c79b27e00087f88d574",
}
PER_PART = 396
HEADER = re.compile(r"#begin document \((nw/test_type[12]/(?:not_)?stereotype//(\d+))\); part 000")
SINGLE = re.compile(r"\((\d+)\)")
OPEN = re.compile(r"\((\d+)")
CLOSE = re.compile(r"(\d+)\)")


def metadata():
    return json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))


def collect_docs(lines, part, source_url):
    docs = []
    doc_id = None
    kind, condition = part.split("-")
    label = "not_stereotype" if condition == "anti" else "stereotype"
    for line_number, row in enumerate(lines, start=1):
        if not row.strip():
            continue
        if doc_id is None:
            header = HEADER.fullmatch(row)
            if header is None or not header[1].startswith(f"nw/test_{kind}/{label}//"):
                raise ValueError(f"{part}:{line_number}: unexpected document header")
            doc_id = header[1]
            doc_number = int(header[2])
            start_line = line_number
            tokens, clusters, pending = [], defaultdict(list), defaultdict(list)
            continue
        if row == "#end document":
            solution = json.dumps([sorted(spans) for spans in clusters.values()])
            if not tokens or not clusters or any(pending.values()) or parse_clusters(solution, len(tokens)) is None:
                raise ValueError(f"{doc_id}: incomplete reference clusters")
            source = f"{source_url}#L{start_line}-L{line_number}"
            docs.append({
                "key": f"{part}-{doc_number:03}",
                "prompt": numbered_tokens(tokens),
                "solution": solution,
                "prompt_source_url": source,
                "solution_source_url": source,
            })
            doc_id = None
            continue

        fields = row.split("\t")
        index = len(tokens)
        if len(fields) != 15 or fields[:3] != [doc_id, "0", str(index)] or not fields[3]:
            raise ValueError(f"{part}:{line_number}: invalid token row")
        tokens.append(fields[3])
        if fields[-1] == "-":
            continue
        for marker in fields[-1].split("|"):
            if match := SINGLE.fullmatch(marker):
                clusters[match[1]].append([index, index])
            elif match := OPEN.fullmatch(marker):
                pending[match[1]].append(index)
            elif (match := CLOSE.fullmatch(marker)) and pending[match[1]]:
                clusters[match[1]].append([pending[match[1]].pop(), index])
            else:
                raise ValueError(f"{part}:{line_number}: invalid mention marker {marker!r}")
    keys = {doc["key"] for doc in docs}
    if doc_id is not None or len(docs) != PER_PART or keys != {f"{part}-{i:03}" for i in range(PER_PART)}:
        raise ValueError(f"{part}: expected exactly {PER_PART} complete documents with IDs 0–{PER_PART - 1}")
    return docs


def load_tasks(local_dir=None):
    revision = metadata()["dataset_revision"]
    raw = f"https://raw.githubusercontent.com/uclanlp/corefBias/{revision}/{DIRECTORY}"
    web = f"https://github.com/uclanlp/corefBias/blob/{revision}/{DIRECTORY}"
    tasks = []
    for part, expected in PARTS.items():
        kind, condition = part.split("-")
        name = f"test_{kind}_{condition}_stereotype.v4_auto_conll"
        if local_dir is None:
            with urlopen(f"{raw}/{name}", timeout=30) as response:
                data = response.read()
        else:
            data = (local_dir / name).read_bytes()
        if sha256(data).hexdigest() != expected:
            raise ValueError(f"{name}: checksum differs from the reviewed snapshot")
        text = data.decode("utf-8")
        tasks.extend(collect_docs(text.splitlines(), part, f"{web}/{name}"))
    return sorted(tasks, key=lambda task: task["key"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-dir", type=Path, help="Directory containing the four pinned CoNLL files")
    args = parser.parse_args()
    tasks = load_tasks(args.local_dir)
    if len(tasks) != metadata()["task_count"]:
        raise ValueError("Imported task count differs from benchmark.json")
    with NamedTemporaryFile(dir=HERE, mode="w", encoding="utf-8", newline="\n", delete=False) as temporary:
        for task in tasks:
            temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
    Path(temporary.name).replace(HERE / "tasks.jsonl")
    print(f"Imported {len(tasks):,} WinoBias test documents")


if __name__ == "__main__":
    main()
