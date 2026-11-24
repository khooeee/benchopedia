#!/usr/bin/env python3
"""Import all five released CLRS-Text evaluation seeds for lcs_length."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from shutil import copyfileobj
from tempfile import NamedTemporaryFile, TemporaryFile
from urllib.request import urlopen

from pyarrow import parquet

from eval import MATRIX


HERE = Path(__file__).resolve().parent
DATASET = "smcleish/CLRS-Text-test"
ALGORITHM = "lcs_length"
SEEDS = {
    1: (100400, "7cc96ef25201d7e7dad3b78e8cecdb0775654b85b940a402d5d27b02f5bea5d2"),
    2: (100600, "a8bc56471b861363e501cfbc0c50eebb5975d673e07202631826fff584bc26ea"),
    3: (100600, "be325e2e0e3d0d50fa6914f93bcd38379066936dc107c4598244422f12e91dfe"),
    4: (100800, "a68d2f4a1c0c8f43ad559131680ec9987627af4ccd8a097ed70efc8e2fd2b712"),
    5: (100400, "eba9fd08dde19ffac87f49db5e344c347296194b45e7f98a255c3d9511e01552"),
}


def load_seed(file, seed, source):
    expected_count, expected_checksum = SEEDS[seed]
    digest = sha256()
    for block in iter(lambda: file.read(1024 * 1024), b""):
        digest.update(block)
    if digest.hexdigest() != expected_checksum:
        raise ValueError(f"test_{seed}: shard checksum differs from the reviewed release")
    file.seek(0)

    shard = parquet.ParquetFile(file)
    if shard.metadata.num_rows != expected_count:
        raise ValueError(f"test_{seed}: unexpected shard row count")
    tasks, lengths = [], {}
    counts = Counter()
    number = 0
    for batch in shard.iter_batches(batch_size=4096, columns=["algo_name", "length", "question", "answer"]):
        for row in batch.to_pylist():
            number += 1
            if row["algo_name"] != ALGORITHM:
                continue
            key = f"test-{seed}-{number:06d}"
            question, gold = row["question"], row["answer"]
            if not isinstance(question, str) or not isinstance(gold, str):
                raise ValueError(f"{key}: missing CLRS-Text question or answer")
            _, separator, final = gold.rpartition(" | ")
            final = final.strip()
            length = row["length"]
            if (not question.startswith("lcs_length:\n") or not question.endswith("\ntrace | b:\n")
                    or not separator or not MATRIX.fullmatch(final) or type(length) is not int):
                raise ValueError(f"{key}: unexpected LCS record format")
            tasks.append({
                "key": key,
                "prompt": question,
                "solution": final,
                "prompt_source_url": source,
                "solution_source_url": source,
            })
            lengths[key] = length
            counts[length] += 1
    if counts != {length: 100 for length in range(4, 16)} or number != expected_count:
        raise ValueError(f"test_{seed}: incomplete LCS length groups")
    return tasks, lengths


def load_evaluation(local_dir=None):
    metadata = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = metadata["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must identify an immutable Hugging Face commit")
    dataset = f"https://huggingface.co/datasets/{DATASET}"
    tasks, lengths = [], {}
    for seed in SEEDS:
        filename = f"test_{seed}-00000-of-00001.parquet"
        source = f"{dataset}/blob/{revision}/data/{filename}"
        if local_dir is None:
            url = f"{dataset}/resolve/{revision}/data/{filename}"
            with TemporaryFile() as file, urlopen(url, timeout=60) as response:
                copyfileobj(response, file)
                file.seek(0)
                records, record_lengths = load_seed(file, seed, source)
        else:
            with (local_dir / filename).open("rb") as file:
                records, record_lengths = load_seed(file, seed, source)
        tasks.extend(records)
        lengths.update(record_lengths)
    if len(tasks) != metadata["task_count"]:
        raise ValueError("Imported task count differs from benchmark.json")
    return tasks, lengths


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--local-dir", type=Path, help="Use local copies of all five pinned Parquet files")
    args = parser.parse_args()
    tasks, _ = load_evaluation(args.local_dir)
    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False) as temporary:
        for task in tasks:
            temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
    Path(temporary.name).replace(HERE / "tasks.jsonl")
    print(f"Imported {len(tasks):,} CLRS-Text LCS test tasks")


if __name__ == "__main__":
    main()
