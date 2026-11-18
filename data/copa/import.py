"""Import the 500 questions of the COPA test set.

Run from the repository root: python3 data/copa/import.py
Only Python's standard library is required. The published package carries no
version history, so it is pinned by the SHA-256 digest in benchmark.json; the
importer refuses to write anything if the download does not match it.
"""

import hashlib
import json
import re
import sys
import tarfile
import tempfile
import urllib.request
import xml.etree.ElementTree as ElementTree
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
# The publisher's address for the package,
# https://people.ict.usc.edu/~gordon/downloads/COPA-resources.tgz, no longer
# answers. This is the Internet Archive's unmodified capture of that file.
ARCHIVE_URL = ("https://web.archive.org/web/20230117124437id_/"
               "https://people.ict.usc.edu/~gordon/downloads/COPA-resources.tgz")
QUESTIONS_MEMBER = "COPA-resources/datasets/copa-test.xml"
GOLD_MEMBER = "COPA-resources/results/gold.test"
EXPECTED_IDS = range(501, 1001)
EXPECTED_DIRECTIONS = {"cause": 250, "effect": 250}
EXPECTED_ANSWERS = {"1": 250, "2": 250}
# The questions the publisher's readable question file asks for each direction.
QUESTIONS = {"cause": "What was the CAUSE of this?",
             "effect": "What happened as a RESULT?"}
GOLD_LINE = re.compile(r"(\d+) (1 0|0 1)")


def download(url, checksum, path):
    """Stream the published package to disk and check it is the pinned revision."""
    digest = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=600) as response, path.open("wb") as out:
        while chunk := response.read(1 << 20):
            digest.update(chunk)
            out.write(chunk)
    if digest.hexdigest() != checksum:
        sys.exit(f"{url} has digest {digest.hexdigest()}, not the reviewed {checksum}.")


def read_member(archive, name):
    member = archive.getmember(name)
    if not member.isfile():
        sys.exit(f"{name} is not a regular file in the package.")
    return archive.extractfile(member).read()


def questions(package_path):
    """Yield each test question with its answer, after checking its shape."""
    with tarfile.open(package_path, "r:gz") as archive:
        corpus = ElementTree.fromstring(read_member(archive, QUESTIONS_MEMBER))
        gold_text = read_member(archive, GOLD_MEMBER).decode("ascii")
    if corpus.tag != "copa-corpus" or corpus.get("version") != "1.0":
        sys.exit(f"{QUESTIONS_MEMBER} is not a version 1.0 COPA corpus.")
    gold = {}
    for line in gold_text.splitlines():
        if not line.strip():
            continue
        matched = GOLD_LINE.fullmatch(line.strip())
        if matched is None or matched.group(1) in gold:
            sys.exit(f"{GOLD_MEMBER}: unexpected line {line!r}.")
        gold[matched.group(1)] = "1" if matched.group(2) == "1 0" else "2"
    if sorted(gold) != sorted(item.get("id") for item in corpus):
        sys.exit(f"{GOLD_MEMBER} does not answer exactly the questions of {QUESTIONS_MEMBER}.")
    for item in corpus:
        number = item.get("id")
        if item.tag != "item" or [child.tag for child in item] != ["p", "a1", "a2"]:
            sys.exit(f"item {number}: expected a premise and two alternatives.")
        if item.get("asks-for") not in QUESTIONS:
            sys.exit(f"item {number}: unexpected direction {item.get('asks-for')!r}.")
        answer = item.get("most-plausible-alternative")
        if answer not in EXPECTED_ANSWERS or gold.get(number) != answer:
            sys.exit(f"item {number}: the answer differs from {GOLD_MEMBER}.")
        for child in item:
            if child.text is None or not child.text.strip() or "\n" in child.text:
                sys.exit(f"item {number}: empty or multi-line {child.tag}.")
        yield item


def to_task(item):
    premise, first, second = (child.text for child in item)
    answer = item.get("most-plausible-alternative")
    return {
        "key": item.get("id"),
        "prompt": (f"Premise: {premise} {QUESTIONS[item.get('asks-for')]}\n\n"
                   f"Alternative 1: {first}\n\nAlternative 2: {second}"),
        "solution": f"Alternative {answer}: {first if answer == '1' else second}",
        "prompt_source_url": ARCHIVE_URL,
        "solution_source_url": ARCHIVE_URL,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{64}", revision):
        sys.exit("dataset_revision must be the SHA-256 digest of the published package.")
    if benchmark["task_count"] != len(EXPECTED_IDS):
        sys.exit(f"The declared scope must be all {len(EXPECTED_IDS)} test questions.")
    directions = {direction: 0 for direction in EXPECTED_DIRECTIONS}
    answers = {answer: 0 for answer in EXPECTED_ANSWERS}
    tasks = []
    with tempfile.TemporaryDirectory() as workspace:
        package = Path(workspace) / "COPA-resources.tgz"
        print(f"Reading {ARCHIVE_URL}")
        download(ARCHIVE_URL, revision, package)
        for item in questions(package):
            directions[item.get("asks-for")] += 1
            answers[item.get("most-plausible-alternative")] += 1
            tasks.append(to_task(item))
    if sorted(int(task["key"]) for task in tasks) != list(EXPECTED_IDS):
        sys.exit(f"Expected the questions numbered {EXPECTED_IDS.start} to "
                 f"{EXPECTED_IDS.stop - 1}, once each.")
    if directions != EXPECTED_DIRECTIONS or answers != EXPECTED_ANSWERS:
        sys.exit(f"Unexpected balance of directions {directions} or answers {answers}.")
    tasks.sort(key=lambda task: int(task["key"]))
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks)} COPA test questions to {out}")


if __name__ == "__main__":
    main()
