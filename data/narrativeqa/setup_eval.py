"""Install the exact English METEOR 1.3 files from the authors' release."""

import argparse
import hashlib
from pathlib import Path
import shutil
import tarfile
import tempfile
from urllib.request import urlopen

from eval import METEOR_FILES, check_setup, metric_dir


RELEASE = "https://www.cs.cmu.edu/~alavie/METEOR/download/meteor-1.3.tgz"
RELEASE_SHA256 = "657bb593c7bd172b71e7c1342c0e91bfbba8bb73c8700d3e59a89a2434e7ddc7"


def install(archive, staging, destination):
    digest = hashlib.sha256()
    with archive.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != RELEASE_SHA256:
        raise SystemExit("METEOR 1.3 archive checksum does not match the pinned release")
    with tarfile.open(archive) as bundle:
        for name, digest in METEOR_FILES.items():
            member = bundle.getmember("meteor-1.3/" + name)
            if not member.isfile():
                raise SystemExit(f"Expected a regular file at {name}")
            content = bundle.extractfile(member).read()
            if hashlib.sha256(content).hexdigest() != digest:
                raise SystemExit(f"Unexpected METEOR 1.3 file: {name}")
            staged = staging / name
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(content)
    for name in METEOR_FILES:
        output = destination / name
        output.parent.mkdir(parents=True, exist_ok=True)
        (staging / name).replace(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="install from an existing copy of the pinned release")
    args = parser.parse_args()
    if check_setup() is None:
        return
    if shutil.which("java") is None:
        raise SystemExit("Install Java before preparing METEOR 1.3")
    destination = metric_dir()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as tmp:
        staging = Path(tmp)
        archive = args.archive
        if archive is None:
            archive = staging / "meteor-1.3.tgz"
            with urlopen(RELEASE, timeout=120) as response, archive.open("wb") as output:
                shutil.copyfileobj(response, output)
        install(archive, staging, destination)


if __name__ == "__main__":
    main()
