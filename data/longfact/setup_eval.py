"""Install the pinned SAFE source, tokenizer data, and CPU dependencies."""

import argparse
from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from zipfile import ZipFile

from eval import REVISION, runtime


SOURCE = f"https://codeload.github.com/google-deepmind/long-form-factuality/tar.gz/{REVISION}"
SOURCE_SHA256 = "8776e1770b80a9e7c0564e60d77ed815e1982cdedf7ead78bd57746db43330d4"
PUNKT = ("https://raw.githubusercontent.com/nltk/nltk_data/56512418f6793e31825003ca5b5c5e1ceed0547b/"
         "packages/tokenizers/punkt.zip")
PUNKT_SHA256 = "51c3078994aeaf650bfc8e028be4fb42b4a0d177d41c012b6a983979653660ec"


def fetch(path, url, checksum):
    with urlopen(url, timeout=120) as response, path.open("wb") as stream:
        shutil.copyfileobj(response, stream)
    verify(path, checksum)


def verify(path, checksum):
    if sha256(path.read_bytes()).hexdigest() != checksum:
        raise ValueError(f"SHA-256 mismatch for {path.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="use a local copy of the pinned SAFE archive")
    args = parser.parse_args()
    location = runtime()
    location.mkdir(parents=True, exist_ok=True)
    ready = location / "ready"
    ready.unlink(missing_ok=True)
    sources = location / "upstream"
    target = location / "nltk_data/tokenizers"
    with TemporaryDirectory(dir=location) as directory:
        staging = Path(directory)
        if not sources.exists():
            archive = args.archive
            if archive is None:
                archive = staging / "source.tar.gz"
                fetch(archive, SOURCE, SOURCE_SHA256)
            else:
                verify(archive, SOURCE_SHA256)
            with tarfile.open(archive) as tar:
                for member in tar.getmembers():
                    if not (member.isfile() or member.isdir()) or not (
                        (staging / member.name).resolve().is_relative_to(staging)
                    ):
                        raise ValueError(f"Unexpected SAFE archive entry {member.name}")
                tar.extractall(staging)
            (staging / f"long-form-factuality-{REVISION}").replace(sources)
        if not (target / "punkt/PY3/english.pickle").is_file():
            archive = staging / "punkt.zip"
            fetch(archive, PUNKT, PUNKT_SHA256)
            with ZipFile(archive) as punkt:
                punkt.extractall(staging)
            target.mkdir(parents=True, exist_ok=True)
            (staging / "punkt").replace(target / "punkt")

    directory = Path(__file__).resolve().parent
    venv = location / "venv"
    python = venv / "bin/python"
    if not python.is_file():
        subprocess.run(["uv", "venv", "--python", "3.10", str(venv)], check=True)
    subprocess.run(["uv", "pip", "install", "--python", str(python), "-r",
                    str(directory / "safe-requirements.txt")], check=True)
    subprocess.run([str(python), str(directory / "safe_worker.py"), "--check"], check=True,
                   cwd=sources, env=os.environ | {"NLTK_DATA": str(location / "nltk_data")})
    ready.write_text(REVISION + "\n")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
