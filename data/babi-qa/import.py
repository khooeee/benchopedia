"""Import the checksum-pinned v1.2 English en-10k test questions."""

from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
import re
import tarfile
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
ARCHIVE_URL = "https://dl.fbaipublicfiles.com/parlai/babi/babi.tar.gz"
TEST_MEMBER = re.compile(r"tasks_1-20_v1-2/en-10k/qa(\d+)_[a-z0-9-]+_test\.txt")
QUESTIONS_PER_CATEGORY = 1_000
CATEGORIES = set(range(1, 21))


def read_category(stream, category):
    statements = []
    expected_line = 1
    rows = []
    for raw_line in stream:
        line = raw_line.decode("utf-8").rstrip("\r\n")
        number, content = line.split(" ", 1)
        index = int(number)
        if index == 1:
            statements = []
            expected_line = 1
        if index != expected_line:
            raise ValueError(f"qa{category}: unexpected story line {index}")
        expected_line += 1

        fields = content.split("\t")
        if len(fields) == 1 and content:
            statements.append(content)
            continue
        if len(fields) != 3 or not all(field.strip() for field in fields) or not statements:
            raise ValueError(f"qa{category}: invalid question at story line {index}")
        question, answer, _ = fields
        context = "\n".join(statements)
        rows.append({
            "key": f"qa{category:02d}-{len(rows) + 1:04d}",
            "prompt": f"{context}\n\nQuestion: {question}",
            "solution": answer,
            "prompt_source_url": ARCHIVE_URL,
        })

    if len(rows) != QUESTIONS_PER_CATEGORY:
        raise ValueError(f"qa{category}: expected {QUESTIONS_PER_CATEGORY} questions, got {len(rows)}")
    return rows


def main():
    metadata = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    with urlopen(ARCHIVE_URL, timeout=60) as response:
        payload = response.read()
    revision = f"sha256:{sha256(payload).hexdigest()}"
    if revision != metadata["dataset_revision"]:
        raise ValueError(f"Archive checksum does not match benchmark.json: {revision}")

    categories = {}
    with tarfile.open(fileobj=BytesIO(payload), mode="r:gz") as archive:
        for member in archive.getmembers():
            match = TEST_MEMBER.fullmatch(member.name)
            if not match:
                continue
            category = int(match[1])
            if not member.isfile() or category in categories:
                raise ValueError(f"Duplicate or invalid test file: {member.name}")
            with archive.extractfile(member) as stream:
                categories[category] = read_category(stream, category)
    if categories.keys() != CATEGORIES:
        raise ValueError(f"Archive does not have all 20 test categories: {sorted(categories)}")

    rows = [row for key in sorted(categories) for row in categories[key]]
    if len(rows) != metadata["task_count"] or len({row["key"] for row in rows}) != len(rows):
        raise ValueError("Imported task count or key uniqueness check failed")

    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=HERE, delete=False) as temporary:
        temporary_path = Path(temporary.name)
        try:
            for row in rows:
                temporary.write(json.dumps(row, ensure_ascii=False) + "\n")
            temporary.close()
            temporary_path.replace(HERE / "tasks.jsonl")
        finally:
            temporary_path.unlink(missing_ok=True)
    print(f"Imported {len(rows):,} questions from {len(categories)} bAbI categories.")


if __name__ == "__main__":
    main()
