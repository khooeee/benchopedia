"""Fetch HealthBench's checksum-pinned scoring inputs for local evaluation."""

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from urllib.request import urlopen

from eval import DATASET_SHA256, DATASET_URL, check_setup, source_path


def main():
    if check_setup() is None:
        return
    target = source_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(dir=target.parent) as temporary:
        staged = Path(temporary) / target.name
        with urlopen(DATASET_URL, timeout=120) as response, staged.open("wb") as stream:
            digest = sha256()
            for block in iter(lambda: response.read(1024 * 1024), b""):
                digest.update(block)
                stream.write(block)
        if digest.hexdigest() != DATASET_SHA256:
            raise SystemExit("HealthBench's published dataset checksum changed.")
        staged.replace(target)


if __name__ == "__main__":
    main()
