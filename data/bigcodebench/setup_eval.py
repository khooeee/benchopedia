"""Install the pinned BigCodeBench image and the small local scoring inputs."""

import argparse
import hashlib
from pathlib import Path
import subprocess
from urllib.request import urlopen

from eval import BOSTON_SHA256, IMAGE, INPUTS_SHA256, boston_path, inputs_path


URL = ("https://huggingface.co/datasets/bigcode/bigcodebench/resolve/"
       "b74c0d0bf70d2c0bc459be537895cca163007f1a/data/v0.1.4-00000-of-00001.parquet")
ARCHIVE_SHA256 = "d9a4965821c9507ebdfb551c288656b2d5fe553234f5183044333ca8a4018267"
BOSTON_URL = "https://lib.stat.cmu.edu/datasets/boston"
EXTRACT = """
import io, json, sys
import pyarrow.parquet as parquet
payload = sys.stdin.buffer.read()
rows = parquet.read_table(io.BytesIO(payload), columns=["task_id", "code_prompt", "canonical_solution"]).to_pylist()
records = {f'bigcodebench-{int(row["task_id"].rsplit("/", 1)[1]):04d}':
           [row["code_prompt"], len(row["canonical_solution"])] for row in rows}
print(json.dumps(records, sort_keys=True, ensure_ascii=False, separators=(",",":")))
"""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    subprocess.run(["docker", "pull", "--platform", "linux/amd64", IMAGE], check=True)
    fixture = boston_path()
    if not fixture.is_file() or hashlib.sha256(fixture.read_bytes()).hexdigest() != BOSTON_SHA256:
        with urlopen(BOSTON_URL, timeout=30) as response:
            boston = response.read()
        if hashlib.sha256(boston).hexdigest() != BOSTON_SHA256:
            raise SystemExit("Boston housing checksum differs from the grader fixture")
        fixture.parent.mkdir(exist_ok=True)
        temporary = fixture.with_suffix(".tmp")
        temporary.write_bytes(boston)
        temporary.replace(fixture)
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
