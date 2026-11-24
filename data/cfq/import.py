#!/usr/bin/env python3
"""Import the three full CFQ v1.1 MCD test splits from Google's release."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
from shutil import copyfileobj
import tarfile
from tempfile import NamedTemporaryFile, TemporaryFile
from urllib.request import urlopen

import ijson

from eval import preprocess_sparql, tokenize_punctuation


HERE = Path(__file__).resolve().parent
RELEASE = "https://storage.googleapis.com/cfq_dataset/cfq1.1.tar.gz"
ARCHIVE_SHA256 = "9280c249962273b1ae2716c5c4dfce8574042fab43e57da704809fe90da7720d"
DATASET_SIZE = 239_357
SPLIT_SIZE = 11_968
SPLIT_MEMBERS = {f"cfq/splits/mcd{i}.json": f"mcd{i}" for i in range(1, 4)}


def metadata():
    return json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))


def read_archive(source):
    digest = sha256()
    for block in iter(lambda: source.read(1024 * 1024), b""):
        digest.update(block)
    if digest.hexdigest() != ARCHIVE_SHA256:
        raise ValueError("CFQ archive checksum differs from the reviewed release")
    source.seek(0)

    records, splits = None, {}
    with tarfile.open(fileobj=source, mode="r|gz") as archive:
        for member in archive:
            if member.name == "cfq/dataset.json":
                if records is not None or not member.isfile():
                    raise ValueError("Unexpected CFQ dataset member")
                with archive.extractfile(member) as data:
                    records = [
                        (sample["questionPatternModEntities"], sample["sparqlPatternModEntities"])
                        for sample in ijson.items(data, "item")
                    ]
            elif member.name in SPLIT_MEMBERS:
                split = SPLIT_MEMBERS[member.name]
                if split in splits or not member.isfile():
                    raise ValueError(f"Unexpected CFQ split member {member.name}")
                with archive.extractfile(member) as data:
                    splits[split] = json.load(data)["testIdxs"]
    if records is None or len(records) != DATASET_SIZE or splits.keys() != set(SPLIT_MEMBERS.values()):
        raise ValueError("Missing or truncated CFQ dataset or split members")
    return records, splits


def load_tasks(local_archive=None):
    config = metadata()
    match = re.fullmatch(r"gcs-generation-(\d+)", config["dataset_revision"])
    if match is None:
        raise ValueError("dataset_revision must identify an immutable Cloud Storage generation")
    release = f"{RELEASE}?generation={match[1]}"
    if local_archive is None:
        with TemporaryFile() as local, urlopen(release, timeout=60) as response:
            copyfileobj(response, local)
            local.seek(0)
            records, splits = read_archive(local)
    else:
        with local_archive.open("rb") as local:
            records, splits = read_archive(local)

    tasks = []
    for split, indices in sorted(splits.items()):
        if (not isinstance(indices, list) or len(indices) != SPLIT_SIZE
                or not all(type(index) is int and 0 <= index < len(records) for index in indices)
                or len(set(indices)) != SPLIT_SIZE):
            raise ValueError(f"{split}: expected {SPLIT_SIZE} distinct test indices")
        for index in sorted(indices):
            key = f"{split}-{index:06d}"
            question, query = records[index]
            if not all(isinstance(value, str) and value.strip() for value in (question, query)):
                raise ValueError(f"{key}: missing text or reference query")
            tasks.append({
                "key": key,
                "prompt": tokenize_punctuation(question),
                "solution": preprocess_sparql(query),
                "prompt_source_url": release,
                "solution_source_url": release,
            })

    if len(tasks) != config["task_count"]:
        raise ValueError("Imported task count differs from benchmark.json")
    return tasks


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Read a local copy of the checksum-pinned release")
    args = parser.parse_args()
    tasks = load_tasks(args.archive)
    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False) as temporary:
        for task in tasks:
            temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
    Path(temporary.name).replace(HERE / "tasks.jsonl")
    print(f"Imported {len(tasks):,} CFQ MCD test records")


if __name__ == "__main__":
    main()
