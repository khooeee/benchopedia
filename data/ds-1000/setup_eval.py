"""Install the pinned DS-1000 tests and build the offline evaluation image."""

import argparse
import hashlib
from pathlib import Path
import subprocess
from urllib.request import urlopen

from eval import ARCHIVE_SHA256, IMAGE, REVISION, archive_path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    archive = archive_path()
    archive.parent.mkdir(exist_ok=True)
    if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        if args.archive:
            payload = args.archive.read_bytes()
        else:
            url = f"https://raw.githubusercontent.com/xlang-ai/DS-1000/{REVISION}/data/ds1000.jsonl.gz"
            with urlopen(url, timeout=120) as response:
                payload = response.read()
        if hashlib.sha256(payload).hexdigest() != ARCHIVE_SHA256:
            raise SystemExit("DS-1000 test archive checksum differs from the pinned release")
        temp = archive.with_suffix(".tmp")
        temp.write_bytes(payload)
        temp.replace(archive)
    directory = Path(__file__).resolve().parent
    subprocess.run(["docker", "build", "--platform", "linux/amd64", "-t", IMAGE,
                    "-f", str(directory / "Dockerfile.eval"), str(directory)], check=True)


if __name__ == "__main__":
    main()
