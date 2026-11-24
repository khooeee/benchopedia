#!/usr/bin/env python3
"""Fetch the checksum-pinned local CoNLL scorer and its original dependencies."""

from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.request import urlopen

from eval import SCORER_FILES, SCORER_REVISION, scorer_directory


def main():
    directory = scorer_directory()
    prefix = f"https://raw.githubusercontent.com/conll/reference-coreference-scorers/{SCORER_REVISION}"
    for relative, expected in SCORER_FILES.items():
        path = directory / relative
        if path.is_file() and sha256(path.read_bytes()).hexdigest() == expected:
            continue
        with urlopen(f"{prefix}/{relative}", timeout=30) as response:
            source = response.read()
        if sha256(source).hexdigest() != expected:
            raise ValueError(f"Unexpected checksum for {relative}")
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
            temporary.write(source)
        Path(temporary.name).replace(path)
    print(f"CoNLL scorer v8.01 ready in {directory}")


if __name__ == "__main__":
    main()
