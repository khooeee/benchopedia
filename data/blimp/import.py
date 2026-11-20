"""Import BLiMP: all 67,000 minimal pairs in its 67 paradigms.

Run from the repository root: python3 data/blimp/import.py
Only Python's standard library is required. The paradigm files are fetched from
the BLiMP repository at the commit pinned in benchmark.json, so a rerun
reproduces the same snapshot.
"""

import json
import re
import sys
import urllib.request
from collections import Counter
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "alexwarstadt/blimp"
PARADIGMS = 67
PAIRS = 1000
EXPECTED = PARADIGMS * PAIRS
QUESTION = "Which of these two sentences is grammatically acceptable?"


def fetch(url):
    with urllib.request.urlopen(url, timeout=120) as response:
        return response.read()


def paradigm_files(revision):
    """The .jsonl files in data/ at the revision, from the GitHub API."""
    url = f"https://api.github.com/repos/{REPOSITORY}/contents/data?ref={revision}"
    print(f"Listing {url}")
    names = sorted(entry["name"] for entry in json.loads(fetch(url))
                   if entry["type"] == "file" and entry["name"].endswith(".jsonl"))
    if len(names) != PARADIGMS:
        sys.exit(f"data/: expected {PARADIGMS} paradigm files, found {len(names)}.")
    return names


def to_task(record, line, uid, source):
    where = f"{uid} line {line}"
    good, bad = record["sentence_good"], record["sentence_bad"]
    for sentence in (good, bad):
        if not isinstance(sentence, str) or not sentence.strip() or sentence != sentence.strip():
            sys.exit(f"{where}: unexpected sentence {sentence!r}.")
    # Alternate the acceptable sentence between the two positions, first for
    # even pair numbers and second for odd ones, so position carries no signal.
    pair = int(record["pairID"])
    options = (good, bad) if pair % 2 == 0 else (bad, good)
    answer = 1 if pair % 2 == 0 else 2
    url = f"{source}#L{line}"
    return {
        "key": f"{uid}-{pair}",
        "prompt": f"{QUESTION}\n\n1. {options[0]}\n2. {options[1]}",
        "solution": f"{answer}. {good}",
        "prompt_source_url": url,
        "solution_source_url": url,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be a full Git commit SHA.")
    if benchmark["task_count"] != EXPECTED:
        sys.exit(f"The declared scope must be all {EXPECTED:,} minimal pairs.")
    tasks = []
    for name in paradigm_files(revision):
        uid = name.removesuffix(".jsonl")
        text = fetch(f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/data/{name}").decode("utf-8")
        records = [json.loads(line) for line in text.splitlines()]
        if len(records) != PAIRS:
            sys.exit(f"{name}: expected {PAIRS} pairs, found {len(records)}.")
        source = f"https://github.com/{REPOSITORY}/blob/{revision}/data/{name}"
        for line, record in enumerate(records, 1):
            if record["UID"] != uid or record["pairID"] != str(line - 1):
                sys.exit(f"{name} line {line}: expected paradigm {uid} pair {line - 1}.")
            tasks.append(to_task(record, line, uid, source))
    if len(tasks) != EXPECTED:
        sys.exit(f"Expected {EXPECTED:,} pairs, found {len(tasks):,}.")
    if len({task["key"] for task in tasks}) != len(tasks):
        sys.exit("Keys are not unique.")
    answers = Counter(task["solution"].split(".", 1)[0] for task in tasks)
    if answers["1"] != answers["2"]:
        sys.exit(f"Answer positions are not balanced: {dict(answers)}.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} BLiMP minimal pairs to {out}")


if __name__ == "__main__":
    main()
