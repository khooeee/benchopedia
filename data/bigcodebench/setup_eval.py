"""Install the pinned BigCodeBench image and the small local scoring inputs."""

import argparse
import hashlib
from pathlib import Path
import subprocess
from urllib.request import urlopen
from uuid import uuid4
from zipfile import ZipFile

from eval import (BOSTON_SHA256, DOWNLOADS, IMAGE, INPUTS_SHA256, NLTK_FIXTURES,
                  boston_path, inputs_path, matches_checksum, nltk_path)


URL = ("https://huggingface.co/datasets/bigcode/bigcodebench/resolve/"
       "b74c0d0bf70d2c0bc459be537895cca163007f1a/data/v0.1.4-00000-of-00001.parquet")
ARCHIVE_SHA256 = "d9a4965821c9507ebdfb551c288656b2d5fe553234f5183044333ca8a4018267"
BOSTON_URL = "https://lib.stat.cmu.edu/datasets/boston"
NLTK_URL = "https://raw.githubusercontent.com/nltk/nltk_data/56512418f6793e31825003ca5b5c5e1ceed0547b/packages/"
EXTRACT = """
import io, json, sys
import pyarrow.parquet as parquet
payload = sys.stdin.buffer.read()
rows = parquet.read_table(io.BytesIO(payload), columns=["task_id", "code_prompt", "canonical_solution"]).to_pylist()
records = {f'bigcodebench-{int(row["task_id"].rsplit("/", 1)[1]):04d}':
           [row["code_prompt"], len(row["canonical_solution"])] for row in rows}
print(json.dumps(records, sort_keys=True, ensure_ascii=False, separators=(",",":")))
"""


def install_fixture(target, url, digest):
    if matches_checksum(target, digest):
        return
    with urlopen(url, timeout=45) as response:
        payload = response.read()
    if hashlib.sha256(payload).hexdigest() != digest:
        raise SystemExit(f"{target.name}: checksum differs from the pinned fixture")
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(f".{uuid4().hex}.tmp")
    try:
        temporary.write_bytes(payload)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    subprocess.run(["docker", "build", "--platform", "linux/amd64", "-f", str(directory / "dockerfile.eval"),
                    "-t", IMAGE, str(directory)], check=True)
    install_fixture(boston_path(), BOSTON_URL, BOSTON_SHA256)
    for name, (url, digest) in DOWNLOADS.items():
        install_fixture(inputs_path().with_name(name), url, digest)
    for name, digest in NLTK_FIXTURES.items():
        archive = nltk_path() / name
        install_fixture(archive, NLTK_URL + name, digest)
        if name != "sentiment/vader_lexicon.zip":
            with ZipFile(archive) as package:
                package.extractall(archive.parent)
    target = inputs_path()
    if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == INPUTS_SHA256:
        return
    if args.archive:
        payload = args.archive.read_bytes()
    else:
        with urlopen(URL, timeout=120) as response:
            payload = response.read()
    if hashlib.sha256(payload).hexdigest() != ARCHIVE_SHA256:
        raise SystemExit("BigCodeBench dataset checksum differs from the pinned v0.1.4 release")
    result = subprocess.run(
        ["docker", "run", "--rm", "--platform", "linux/amd64", "--network", "none",
         "--entrypoint", "python3", "-i", IMAGE, "-B", "-c", EXTRACT],
        input=payload, stdout=subprocess.PIPE, check=True, timeout=120,
    )
    if hashlib.sha256(result.stdout).hexdigest() != INPUTS_SHA256:
        raise SystemExit("BigCodeBench extracted scoring data checksum differs")
    target.parent.mkdir(exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(result.stdout)
    temporary.replace(target)


if __name__ == "__main__":
    main()
