"""Import the 10,000 sentence pairs of the SNLI 1.0 test split.

Run from the repository root: python3 data/snli/import.py
Only Python's standard library is required. The 1.0 distribution carries no
version history, so the archive is pinned by the SHA-256 digest in
benchmark.json; the importer refuses to write anything if it does not match.
"""

import hashlib
import json
import re
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
# The copy the project page names: "SNLI is archived at the NYU Faculty Digital
# Archive." The Stanford download has been unreachable; this one is open.
ARCHIVE_URL = "https://archive.nyu.edu/bitstream/2451/41728/2/snli_1.0.zip"
ARCHIVE_MEMBER = "snli_1.0/snli_1.0_test.jsonl"
RECORD_FIELDS = ["annotator_labels", "captionID", "gold_label", "pairID",
                 "sentence1", "sentence1_binary_parse", "sentence1_parse",
                 "sentence2", "sentence2_binary_parse", "sentence2_parse"]
LABELS = ("entailment", "neutral", "contradiction")
NO_MAJORITY = "-"
EXPECTED_COUNT = 10000
# The counts the distribution's own README states for this split.
EXPECTED_LABELS = {"entailment": 3368, "neutral": 3219, "contradiction": 3237,
                   NO_MAJORITY: 176}
EXPECTED_PREMISES = 3323
QUESTION = "Does the premise entail the hypothesis, contradict it, or neither?"
# A pair identifier is its premise's identifier and the round and label it was
# written for, as in 2677109430.jpg#1r1n.
PAIR_ID = re.compile(r"(?P<caption>\S+\.jpg#\d+)r(?P<round>\d+)(?P<label>[enc])")


def download(url, checksum, path):
    """Stream the published archive to disk and check it is the pinned revision."""
    digest = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=1200) as response, path.open("wb") as out:
        while chunk := response.read(1 << 20):
            digest.update(chunk)
            out.write(chunk)
    if digest.hexdigest() != checksum:
        sys.exit(f"{url} has digest {digest.hexdigest()}, not the reviewed {checksum}.")


def pairs(archive_path):
    """Yield each pair of the test split, after checking its shape."""
    with zipfile.ZipFile(archive_path) as archive:
        if ARCHIVE_MEMBER not in archive.namelist():
            sys.exit(f"{ARCHIVE_URL}: no {ARCHIVE_MEMBER} in the archive.")
        with archive.open(ARCHIVE_MEMBER) as stream:
            for number, line in enumerate(stream, start=1):
                if not line.strip():
                    continue
                record = json.loads(line)
                if sorted(record) != RECORD_FIELDS:
                    sys.exit(f"line {number}: expected the fields {RECORD_FIELDS}.")
                matched = PAIR_ID.fullmatch(record["pairID"])
                if matched is None or matched.group("caption") != record["captionID"]:
                    sys.exit(f"line {number}: unexpected pair identifier "
                             f"{record['pairID']!r}.")
                if record["gold_label"] not in LABELS + (NO_MAJORITY,):
                    sys.exit(f"line {number}: unexpected label {record['gold_label']!r}.")
                for field in ("sentence1", "sentence2"):
                    if not record[field].strip() or "\n" in record[field]:
                        sys.exit(f"line {number}: empty or multi-line {field}.")
                judgements = [label for label in record["annotator_labels"] if label]
                if len(judgements) != len(record["annotator_labels"]):
                    sys.exit(f"line {number}: a blank annotator label.")
                if not 1 <= len(judgements) <= 5:
                    sys.exit(f"line {number}: {len(judgements)} annotator labels.")
                if any(label not in LABELS for label in judgements):
                    sys.exit(f"line {number}: unexpected annotator label.")
                majority = [label for label in LABELS
                            if judgements.count(label) * 2 > len(judgements)]
                recorded = [] if record["gold_label"] == NO_MAJORITY else [record["gold_label"]]
                if majority != recorded:
                    sys.exit(f"line {number}: the gold label is not the annotators' majority.")
                yield record


def to_task(record):
    gold = record["gold_label"]
    if gold == NO_MAJORITY:
        gold = f"{NO_MAJORITY} (no majority label)"
    return {
        "key": record["pairID"],
        "prompt": (f"Premise: {record['sentence1']}\n\n"
                   f"Hypothesis: {record['sentence2']}\n\n{QUESTION}"),
        "solution": f"{gold}\n\nAnnotator labels: "
                    f"{', '.join(record['annotator_labels'])}",
        "prompt_source_url": ARCHIVE_URL,
        "solution_source_url": ARCHIVE_URL,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{64}", revision):
        sys.exit("dataset_revision must be the SHA-256 digest of the published archive.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit(f"The declared scope must be all {EXPECTED_COUNT} test pairs.")
    labels = {label: 0 for label in EXPECTED_LABELS}
    premises = set()
    tasks = []
    with tempfile.TemporaryDirectory() as workspace:
        archive = Path(workspace) / "snli_1.0.zip"
        print(f"Reading {ARCHIVE_URL}; this is 90 MB.")
        download(ARCHIVE_URL, revision, archive)
        for record in pairs(archive):
            labels[record["gold_label"]] += 1
            premises.add(record["captionID"])
            tasks.append(to_task(record))
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit(f"Expected {EXPECTED_COUNT} pairs with distinct identifiers, "
                 f"found {len(tasks)}.")
    if labels != EXPECTED_LABELS:
        sys.exit(f"Label counts differ from the declared scope: {labels}.")
    if len(premises) != EXPECTED_PREMISES:
        sys.exit(f"Expected {EXPECTED_PREMISES} premises, found {len(premises)}.")
    tasks.sort(key=lambda task: task["key"])
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} SNLI test pairs over {len(premises):,} premises to {out}")


if __name__ == "__main__":
    main()
