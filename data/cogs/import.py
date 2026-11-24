"""Import the complete corrected COGS generalization split."""

from collections import Counter
from hashlib import sha256
from io import StringIO
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
REPO = "najoungkim/COGS"
GEN_FILE = "data/gen.tsv"
GEN_SHA256 = "d013d9eee0bafc153f8decc85f42814ac97260f84964d980e1e2b84577b82361"


def load_tasks(payload, revision):
    if sha256(payload).hexdigest() != GEN_SHA256:
        raise ValueError("The COGS generalization file does not match its pinned SHA-256")
    source = f"https://github.com/{REPO}/blob/{revision}/{GEN_FILE}"
    counts = Counter()
    tasks = []
    with StringIO(payload.decode("utf-8"), newline="") as lines:
        for number, line in enumerate(lines, 1):
            fields = line.rstrip("\r\n").split("\t")
            if len(fields) != 3 or not all(field.strip() for field in fields):
                raise ValueError(f"Invalid COGS row at line {number}")
            sentence, logical_form, case = fields
            counts[case] += 1
            permalink = f"{source}#L{number}"
            tasks.append({
                "key": f"cogs-{number:05d}",
                "prompt": sentence,
                "solution": logical_form,
                "prompt_source_url": permalink,
                "solution_source_url": permalink,
            })
    if len(counts) != 21 or any(count != 1000 for count in counts.values()):
        raise ValueError("Expected 1,000 examples in each of 21 generalization cases")
    if len({task["key"] for task in tasks}) != len(tasks):
        raise ValueError("COGS task keys must be unique")
    return tasks


def main():
    benchmark = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must be an immutable Git commit")
    url = f"https://raw.githubusercontent.com/{REPO}/{revision}/{GEN_FILE}"
    with urlopen(url, timeout=60) as response:
        tasks = load_tasks(response.read(), revision)
    if len(tasks) != benchmark["task_count"]:
        raise ValueError(f"Expected {benchmark['task_count']} tasks, got {len(tasks)}")

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
    print(f"Imported {len(tasks):,} COGS generalization examples.")


if __name__ == "__main__":
    main()
