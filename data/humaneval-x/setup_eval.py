"""Install the original HumanEval-X execution environment and metadata."""

import gzip
import hashlib
import json
import subprocess
from urllib.request import urlopen

from eval import IMAGE, INPUTS_SHA256, inputs_path


BASE = ("https://raw.githubusercontent.com/zai-org/CodeGeeX/2838420b7b4492cf3d16bce5320e26e65960c9e2/"
        "codegeex/benchmark/humaneval-x")
DIGESTS = {
    "python": "5752fb122efddb0e9b47c77907ae6ce9a15aac4dea14e44c46032c831e6b987a",
    "cpp": "dcf2e280a1e91bbc3c5f90edb41397e8a9ac1ccc9f5d2b70082f0b0fbfb6dbb0",
    "java": "276f36db2eb7aeb864f36a19a2f4e1bb2460fb6e22ff100f0b5bedabe3799967",
    "js": "fe5d467f2c1a027b3f6f18d3729aca01f6458c1de2e2d1292a019c5aa9bed424",
    "go": "09126ef64ac68f87296c5f3781186aedc5dec799b114d9df99d6de4a715a7830",
}


def main():
    subprocess.run(["docker", "pull", "--platform", "linux/amd64", IMAGE], check=True)
    target = inputs_path()
    if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == INPUTS_SHA256:
        return
    keys = {}
    for language, expected in DIGESTS.items():
        url = f"{BASE}/{language}/data/humaneval_{language}.jsonl.gz"
        with urlopen(url, timeout=60) as stream:
            archive = stream.read()
        if hashlib.sha256(archive).hexdigest() != expected:
            raise SystemExit(f"HumanEval-X archive differs from the pinned {language} release")
        slug = "javascript" if language == "js" else language
        for i, row in enumerate(map(json.loads, gzip.decompress(archive).decode("utf-8").split("\n")[:-1])):
            extra = [row["import"], row["test_setup"]] if language == "go" else []
            keys[f"{slug}-{i:03d}"] = [len(row["canonical_solution"]), *extra]
    payload = json.dumps(keys, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode() + b"\n"
    if hashlib.sha256(payload).hexdigest() != INPUTS_SHA256:
        raise SystemExit("HumanEval-X extracted metadata checksum differs")
    target.parent.mkdir(exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(payload)
    temporary.replace(target)


if __name__ == "__main__":
    main()
