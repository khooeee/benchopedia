"""Install the pinned BIRD development databases and prepare a local Docker volume."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
from urllib.request import urlopen
from zipfile import ZipFile

from eval import DATABASE_SHA256, IMAGE, VOLUME, data_dir, databases_ready, sha256, volume_ready


RELEASE_URL = ("https://drive.usercontent.google.com/download"
               "?id=13VLWIwpw5E3d5DUkMvzw7hvHE67a4XkG&export=download&confirm=t")
RELEASE_SHA256 = "aeb211c0e39010bbdae3838bb5e8bd27dc446ed77495b1709f85ccc9bf67f2be"
ZIP_PREFIX = "minidev/MINIDEV/dev_databases"
COPY_TO_VOLUME = """
import hashlib
import json
from pathlib import Path
from shutil import copyfile
import sys
from tempfile import NamedTemporaryFile

def checksum(path):
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for part in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(part)
    return digest.hexdigest()

root = Path('/databases')
checksums = json.load(sys.stdin)
for name, expected in checksums.items():
    destination = root / (name + '.sqlite')
    if destination.is_file() and checksum(destination) == expected:
        continue
    with NamedTemporaryFile(dir=root, delete=False) as file:
        stage = Path(file.name)
    try:
        copyfile(Path('/source') / destination.name, stage)
        if checksum(stage) != expected:
            raise SystemExit(f'Unexpected checksum for {name}')
        stage.chmod(0o644)
        stage.replace(destination)
    finally:
        stage.unlink(missing_ok=True)

with NamedTemporaryFile(dir=root, mode='w', delete=False) as file:
    json.dump(checksums, file, sort_keys=True)
marker = Path(file.name)
marker.chmod(0o644)
marker.replace(root / '.checksums.json')
"""


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
    directory = Path(__file__).resolve().parent
    subprocess.run(["docker", "build", "-f", str(directory / "dockerfile.eval"), "-t", IMAGE, str(directory)], check=True)
    if not databases_ready():
        prepare_databases(args.archive)
    if not volume_ready():
        subprocess.run(["docker", "volume", "create", VOLUME], check=True)
        subprocess.run(
            ["docker", "run", "--rm", "--pull=never", "--network", "none", "--read-only",
             "--cap-drop", "ALL", "--security-opt", "no-new-privileges",
             "--mount", f"type=bind,src={data_dir()},dst=/source,readonly",
             "--mount", f"type=volume,src={VOLUME},dst=/databases", "-i", IMAGE, "python", "-I", "-c", COPY_TO_VOLUME],
            input=json.dumps(DATABASE_SHA256), text=True, check=True, timeout=120,
        )


if __name__ == "__main__":
    main()
