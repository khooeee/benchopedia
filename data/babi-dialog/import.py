"""Import all response turns in the two bAbI Dialog Task 1 test sets."""

from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
from tarfile import open as open_tar
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
ARCHIVE_DIRECTORY = "dialog-bAbI-tasks"
SPLITS = {
    "oov": ("dialog-babi-task1-API-calls-tst-OOV.txt", 6020),
    "standard": ("dialog-babi-task1-API-calls-tst.txt", 5936),
}


def load_split(data, split, source, candidates, response_count):
    tasks = []
    history = []
    dialogue = 0
    turn = 0
    for line in data.decode("utf-8").splitlines():
        if not line:
            history = []
            turn = 0
            continue
        number, separator, pair = line.partition(" ")
        customer, tab, bot = pair.partition("\t")
        if not separator or not tab or not customer or bot not in candidates or number != str(turn + 1):
            raise ValueError(f"Invalid {split} dialog line after dialog {dialogue}, turn {turn}")
        if turn == 0:
            dialogue += 1
        turn += 1
        history.append("Customer: " + customer)
        tasks.append({
            "key": f"babi-dialog-{split}-{dialogue:04d}-{turn:02d}",
            "prompt": "\n".join(history),
            "solution": bot,
            "prompt_source_url": source,
            "solution_source_url": source,
        })
        history.append("Bot: " + bot)
    if dialogue != 1000 or len(tasks) != response_count:
        raise ValueError(f"{split} must contain 1,000 dialogs and {response_count} response turns")
    return tasks


def main():
    benchmark = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", revision):
        raise ValueError("dataset_revision must give the archive SHA-256")
    source = benchmark["dataset_url"]
    with urlopen(source, timeout=90) as response:
        payload = response.read()
    if "sha256:" + sha256(payload).hexdigest() != revision:
        raise ValueError("Dialog bAbI archive does not match its pinned SHA-256")

    tasks = []
    with open_tar(fileobj=BytesIO(payload), mode="r:gz") as archive:
        candidate_data = archive.extractfile(
            f"{ARCHIVE_DIRECTORY}/dialog-babi-candidates.txt"
        ).read()
        if candidate_data != (HERE / "candidates.txt").read_bytes():
            raise ValueError("The bundled candidate set differs from the pinned archive")
        candidates = {
            line.partition(" ")[2] for line in candidate_data.decode("utf-8").splitlines()
        }
        if len(candidates) != 4212 or "" in candidates:
            raise ValueError("Expected 4,212 distinct candidates")
        for split, (filename, expected) in SPLITS.items():
            data = archive.extractfile(f"{ARCHIVE_DIRECTORY}/{filename}").read()
            tasks.extend(load_split(data, split, source, candidates, expected))
    if len(tasks) != benchmark["task_count"] or len({task["key"] for task in tasks}) != len(tasks):
        raise ValueError("Dialog bAbI count or identifiers differ from the declared scope")

    with NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False
    ) as temporary:
        path = Path(temporary.name)
        try:
            for task in tasks:
                temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
            temporary.close()
            path.replace(HERE / "tasks.jsonl")
        finally:
            path.unlink(missing_ok=True)
    print(f"Imported {len(tasks):,} bAbI Dialog Task 1 response turns.")


if __name__ == "__main__":
    main()
