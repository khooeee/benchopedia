"""Prepare the public datasets used by the pinned DS-1000 tests."""

import hashlib
from pathlib import Path
from urllib.request import urlopen

from sklearn.datasets import fetch_california_housing


SEABORN_REVISION = "71e2436a092d714350de0fc409ca8a8714e7e78f"
FIXTURES = {
    "exercise": "d67ff5896d7d262bba3ec0bd7a8db410e56afc96a0436e08dfe53016d5f1e4e6",
    "penguins": "e07636bd8af74260099ea2f8678e2eabbf35def579940cc76f67061ee16c06c1",
    "planets": "a6d10044887e17396974525a366f5fa2e4b34df70f491e64eb9943de0e3d3825",
    "tips": "e54cc4d2ce1bff65d32ca60b3e4b802e06bde1d7e7caf6f796f6bf7370e863b0",
}


def main():
    root = Path("/opt/ds1000-fixtures")
    for name, expected in FIXTURES.items():
        revision_url = f"https://raw.githubusercontent.com/mwaskom/seaborn-data/{SEABORN_REVISION}/{name}.csv"
        with urlopen(revision_url, timeout=60) as response:
            dataset = response.read()
        if hashlib.sha256(dataset).hexdigest() != expected:
            raise SystemExit(f"DS-1000 fixture checksum differs: {name}.csv")
        path = root / "seaborn" / (name + ".csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(dataset)
    fetch_california_housing(data_home=str(root / "sklearn"))


if __name__ == "__main__":
    main()
