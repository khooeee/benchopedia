"""Install the pinned BigCodeBench image and the small local scoring inputs."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
from urllib.request import urlopen

from eval import IMAGE, INPUTS_SHA256, inputs_path


URL = ("https://huggingface.co/datasets/bigcode/bigcodebench/resolve/"
       "b74c0d0bf70d2c0bc459be537895cca163007f1a/data/v0.1.4-00000-of-00001.parquet")
ARCHIVE_SHA256 = "d9a4965821c9507ebdfb551c288656b2d5fe553234f5183044333ca8a4018267"
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
