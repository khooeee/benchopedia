"""Install the pinned IFEval evaluator in the local build directory."""

import io
from pathlib import Path
import subprocess
import sys
import urllib.request
import zipfile

from eval import PYTHON, READY, REVISION, RUNTIME, UPSTREAM

SCORER_URL = (
    "https://raw.githubusercontent.com/google-research/google-research/"
    f"{REVISION}/instruction_following_eval"
)
SCORER_FILES = (
    "evaluation_lib.py", "instructions.py", "instructions_registry.py",
    "instructions_util.py", "data/input_data.jsonl",
)
DEPENDENCIES = (
    "absl-py==2.3.1", "langdetect==1.0.9", "immutabledict==4.2.1", "nltk==3.10.4",
)
PUNKT_URL = (
    "https://raw.githubusercontent.com/nltk/nltk_data/4f15a3d89eefe9748ec1c05be495d91289197155/"
    "packages/tokenizers/punkt_tab.zip"
)


def download(url):
    with urllib.request.urlopen(url, timeout=30) as response:
        return response.read()


def main():
    READY.unlink(missing_ok=True)
    subprocess.run([sys.executable, "-m", "venv", str(PYTHON.parent.parent)], check=True)
    subprocess.run([str(PYTHON), "-m", "pip", "install", *DEPENDENCIES], check=True)

    for filename in SCORER_FILES:
        path = UPSTREAM / "instruction_following_eval" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(download(f"{SCORER_URL}/{filename}"))

    tokenizer = RUNTIME / "nltk_data" / "tokenizers"
    with zipfile.ZipFile(io.BytesIO(download(PUNKT_URL))) as resource:
        for name in ("abbrev_types.txt", "collocations.tab", "ortho_context.tab", "sent_starters.txt"):
            entry = Path("punkt_tab", "english", name)
            path = tokenizer / entry
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(resource.read(entry.as_posix()))
    READY.write_text(REVISION + "\n", encoding="utf-8")
    print(f"Installed the pinned IFEval evaluator in {RUNTIME}")


if __name__ == "__main__":
    main()
