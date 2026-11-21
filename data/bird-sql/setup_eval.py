"""Install the exact development databases linked from the BIRD dataset card."""

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.request import urlopen
from zipfile import ZipFile

from eval import DATABASE_SHA256, IMAGE, data_dir, databases_ready, sha256


RELEASE_URL = ("https://drive.usercontent.google.com/download"
               "?id=13VLWIwpw5E3d5DUkMvzw7hvHE67a4XkG&export=download&confirm=t")
RELEASE_SHA256 = "aeb211c0e39010bbdae3838bb5e8bd27dc446ed77495b1709f85ccc9bf67f2be"
ZIP_PREFIX = "minidev/MINIDEV/dev_databases"


def install(archive, staging, destination):
    if sha256(archive) != RELEASE_SHA256:
        raise SystemExit("BIRD development archive checksum does not match the pinned release")
    with ZipFile(archive) as release:
        for database, expected in DATABASE_SHA256.items():
            name = database + ".sqlite"
            path = staging / name
            with release.open(f"{ZIP_PREFIX}/{database}/{name}") as src, path.open("wb") as target:
                shutil.copyfileobj(src, target)
            if sha256(path) != expected:
                raise SystemExit(f"BIRD development database checksum differs: {name}")
    destination.mkdir(exist_ok=True)
    for database in DATABASE_SHA256:
        name = database + ".sqlite"
        (staging / name).replace(destination / name)


def prepare_databases(archive):
    destination = data_dir()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        staging = Path(tmp)
        if archive is None:
            archive = staging / "bird-db-package.zip"
            with urlopen(RELEASE_URL, timeout=120) as response, archive.open("wb") as output:
                shutil.copyfileobj(response, output)
        install(archive, staging, destination)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    subprocess.run(["docker", "pull", IMAGE], check=True)
    if not databases_ready():
        prepare_databases(args.archive)


if __name__ == "__main__":
    main()
