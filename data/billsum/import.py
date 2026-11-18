"""Import the 3,269 US bills of the official BillSum test split.

Run from the repository root: python3 data/billsum/import.py
Only Python's standard library is required. The published archive carries no
version history, so it is pinned by the SHA-256 digest in benchmark.json; the
importer refuses to write anything if the download does not match it.
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
# The archive the authors' data documentation publishes as the final version of
# the dataset. Google serves it behind a virus-scan warning for files this
# large, which the confirm parameter answers; no account is involved.
ARCHIVE_URL = ("https://drive.usercontent.google.com/download"
               "?id=1g89WgFHMRbr4QrvA0ngh26PY081Nv3lx&export=download&confirm=t")
ARCHIVE_MEMBER = "us_test_data_final_OFFICIAL.jsonl"
RECORD_FIELDS = ["bill_id", "sum_len", "summary", "text", "text_len", "title"]
BILL_ID = re.compile(r"(\d{3})_(hr|s)(\d+)")
CHAMBERS = {"hr": "H.R.", "s": "S."}
EXPECTED_COUNT = 3269
EXPECTED_CONGRESSES = {103: 256, 104: 171, 105: 230, 106: 245, 107: 270,
                       108: 248, 109: 239, 110: 293, 111: 296, 112: 259,
                       113: 261, 114: 297, 115: 204}
EXPECTED_CHAMBERS = {"hr": 2088, "s": 1181}
# The corpus holds mid-length legislation, measured in characters upstream.
MIN_CHARS, MAX_CHARS = 5000, 20000
# Bill text quotes amended law with the typesetter's `` '' marks, so the body
# is fenced rather than left to the prompt renderer. No bill text contains this.
FENCE = "~~~"


def download(url, checksum, path):
    """Stream the published archive to disk and check it is the pinned revision."""
    digest = hashlib.sha256()
    with urllib.request.urlopen(url, timeout=1200) as response, path.open("wb") as out:
        while chunk := response.read(1 << 20):
            digest.update(chunk)
            out.write(chunk)
    if digest.hexdigest() != checksum:
        sys.exit(f"{url} has digest {digest.hexdigest()}, not the reviewed {checksum}.")


def ordinal(number):
    """Return 103rd, 104th and so on, as a Congress is written."""
    if number % 100 in (11, 12, 13):
        return f"{number}th"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
    return f"{number}{suffix}"


def bills(archive_path):
    """Yield each record of the test split, after checking its shape."""
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
                for field in ("title", "text", "summary"):
                    if not record[field].strip():
                        sys.exit(f"line {number}: empty {field}.")
                if "\n" in record["title"] or record["title"] != record["title"].strip():
                    sys.exit(f"line {number}: expected the title on one line.")
                if (record["text_len"] != len(record["text"])
                        or record["sum_len"] != len(record["summary"])):
                    sys.exit(f"line {number}: the recorded lengths do not match the text.")
                if not MIN_CHARS <= len(record["text"]) <= MAX_CHARS:
                    sys.exit(f"line {number}: {len(record['text'])} characters is outside "
                             f"the {MIN_CHARS} to {MAX_CHARS} corpus.")
                if FENCE in record["text"] or record["text"].endswith("\n"):
                    sys.exit(f"line {number}: the bill text cannot be fenced as it stands.")
                yield record


def to_task(record, congress, chamber, number):
    return {
        "key": record["bill_id"],
        "prompt": (f"Summarize this bill: {record['title']}\n\n"
                   f"# Bill\n\n- {CHAMBERS[chamber]} {number}, "
                   f"{ordinal(congress)} Congress\n\n"
                   f"# Bill text\n\n{FENCE}\n{record['text']}\n{FENCE}"),
        "solution": record["summary"],
        "prompt_source_url": ARCHIVE_URL,
        "solution_source_url": ARCHIVE_URL,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{64}", revision):
        sys.exit("dataset_revision must be the SHA-256 digest of the published archive.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit(f"The declared scope must be all {EXPECTED_COUNT} US test bills.")
    congresses = {congress: 0 for congress in EXPECTED_CONGRESSES}
    chambers = {chamber: 0 for chamber in EXPECTED_CHAMBERS}
    tasks = []
    with tempfile.TemporaryDirectory() as workspace:
        archive = Path(workspace) / "billsum.zip"
        print(f"Reading {ARCHIVE_URL}; this is 64 MB.")
        download(ARCHIVE_URL, revision, archive)
        for record in bills(archive):
            matched = BILL_ID.fullmatch(record["bill_id"])
            if matched is None:
                sys.exit(f"{record['bill_id']}: unexpected bill identifier.")
            congress = int(matched.group(1))
            chamber = matched.group(2)
            number = int(matched.group(3))
            if congress not in congresses:
                sys.exit(f"{record['bill_id']}: unexpected Congress.")
            congresses[congress] += 1
            chambers[chamber] += 1
            tasks.append(((congress, chamber, number), to_task(record, congress,
                                                               chamber, number)))
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for _, task in tasks}) != EXPECTED_COUNT:
        sys.exit(f"Expected {EXPECTED_COUNT} bills with distinct identifiers, "
                 f"found {len(tasks)}.")
    if congresses != EXPECTED_CONGRESSES or chambers != EXPECTED_CHAMBERS:
        sys.exit(f"The split differs from the declared scope: {congresses}, {chambers}.")
    tasks = [task for _, task in sorted(tasks, key=lambda pair: pair[0])]
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} BillSum US test bills from the "
          f"{ordinal(min(congresses))} to the {ordinal(max(congresses))} Congress to {out}")


if __name__ == "__main__":
    main()
