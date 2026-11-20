"""Install the original HumanEval-X execution environment and metadata."""

import gzip
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from urllib.request import urlopen
from uuid import uuid4

from eval import GO_FILES, IMAGE, INPUTS_SHA256, go_dir, go_ready, inputs_path


BASE = ("https://raw.githubusercontent.com/zai-org/CodeGeeX/2838420b7b4492cf3d16bce5320e26e65960c9e2/"
        "codegeex/benchmark/humaneval-x")
DIGESTS = {
    "python": "5752fb122efddb0e9b47c77907ae6ce9a15aac4dea14e44c46032c831e6b987a",
    "cpp": "dcf2e280a1e91bbc3c5f90edb41397e8a9ac1ccc9f5d2b70082f0b0fbfb6dbb0",
    "java": "276f36db2eb7aeb864f36a19a2f4e1bb2460fb6e22ff100f0b5bedabe3799967",
    "js": "fe5d467f2c1a027b3f6f18d3729aca01f6458c1de2e2d1292a019c5aa9bed424",
    "go": "09126ef64ac68f87296c5f3781186aedc5dec799b114d9df99d6de4a715a7830",
}


def setup_go():
    if go_ready():
        return
    directory = go_dir()
    directory.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=directory.parent) as staging:
        assets = Path(staging) / "go"
        assets.mkdir()
        for name, expected in GO_FILES.items():
            with urlopen(f"{BASE}/go/evaluation/{name}", timeout=60) as response:
                content = response.read()
            if hashlib.sha256(content).hexdigest() != expected:
                raise SystemExit(f"HumanEval-X {name} checksum differs")
            (assets / name).write_bytes(content)
        warm = 'package humanEval\nimport _ "github.com/go-openapi/inflect"\nimport _ "github.com/stretchr/testify/assert"\n'
        (assets / "warm_test.go").write_text(warm)
        subprocess.run(
            ["docker", "run", "--rm", "--platform", "linux/amd64", "--workdir", "/out",
             "--mount", f"type=bind,src={assets},dst=/out", "-e", "GOMODCACHE=/out/modules",
             "-e", "GOCACHE=/out/cache", "--entrypoint", "/bin/sh", IMAGE, "-c",
             "go mod download && go test -run '^$' warm_test.go"],
            check=True,
        )
        (assets / "warm_test.go").unlink()
        if directory.exists():
            directory.rename(directory.with_name(f"{directory.name}-previous-{uuid4().hex}"))
        assets.rename(directory)


def main():
    subprocess.run(["docker", "pull", "--platform", "linux/amd64", IMAGE], check=True)
    target = inputs_path()
    setup_go()
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
        for i, row in enumerate(map(json.loads, (line for line in gzip.decompress(archive).decode("utf-8").split("\n") if line.strip()))):
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
