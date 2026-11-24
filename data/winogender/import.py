"""Import the complete published Winogender set as matched pronoun variants."""

from collections import defaultdict
import csv
from io import StringIO
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
REPOSITORY = "rudinger/winogender-schemas"
DATASET_FILE = "data/all_sentences.tsv"
GROUP_COUNT = 240
VARIANTS = {
    "male": ("Masculine", re.compile(r"\b(?:he|his|him)\b", re.IGNORECASE)),
    "female": ("Feminine", re.compile(r"\b(?:she|her|hers)\b", re.IGNORECASE)),
    "neutral": ("Neutral", re.compile(r"\b(?:they|their|them|theirs)\b", re.IGNORECASE)),
}
SENTENCE_ID = re.compile(r"([a-z-]+)\.([a-z-]+)\.([01])\.(male|female|neutral)\.txt")


def import_rows(payload, revision):
    entries = csv.DictReader(StringIO(payload, newline=""), delimiter="\t")
    if entries.fieldnames != ["sentid", "sentence"]:
        raise ValueError("Unexpected Winogender sentence columns")

    groups = defaultdict(dict)
    for row in entries:
        parsed_id = SENTENCE_ID.fullmatch(row["sentid"])
        sentence = row["sentence"]
        if not parsed_id or not sentence or len(sentence.splitlines()) != 1:
            raise ValueError(f"Invalid sentence at TSV line {entries.line_num}")
        occupation, participant, answer, variant = parsed_id.groups()
        label, pattern = VARIANTS[variant]
        pronouns = pattern.findall(sentence)
        group = groups[occupation, participant, answer]
        if len(pronouns) != 1 or variant in group:
            raise ValueError(f"Ambiguous pronoun or repeated variant: {row['sentid']}")
        group[variant] = (f"{label} ({pronouns[0]}): {sentence}", entries.line_num)

    if len(groups) != GROUP_COUNT or any(group.keys() != VARIANTS.keys() for group in groups.values()):
        raise ValueError("Expected 240 complete groups of three pronoun variants")

    rows = []
    for number, ((occupation, participant, answer), group) in enumerate(groups.items(), 1):
        if participant == occupation:
            raise ValueError(f"Referent candidates must be distinct: {occupation}")
        variants = "\n".join(group[variant][0] for variant in VARIANTS)
        lines = [group[variant][1] for variant in VARIANTS]
        choices = (f"A. {occupation}", f"B. {participant}", "C. Neither listed mention")
        rows.append({
            "key": f"winogender-{number:03d}",
            "prompt": "\n".join(choices) + "\n\n" + variants,
            "solution": choices[int(answer)],
            "prompt_source_url": (
                f"https://github.com/{REPOSITORY}/blob/{revision}/{DATASET_FILE}"
                f"#L{min(lines)}-L{max(lines)}"
            ),
        })
    return rows


def main():
    metadata = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = metadata["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must be a full Git commit")
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{DATASET_FILE}"
    with urlopen(url, timeout=30) as response:
        tasks = import_rows(response.read().decode("utf-8"), revision)
    if len(tasks) != metadata["task_count"]:
        raise ValueError("Imported task count does not match benchmark.json")

    with NamedTemporaryFile(mode="w", encoding="utf-8", dir=HERE, delete=False) as temporary:
        path = Path(temporary.name)
        try:
            for task in tasks:
                temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
            temporary.close()
            path.replace(HERE / "tasks.jsonl")
        finally:
            path.unlink(missing_ok=True)
    print(f"Imported {len(tasks)} groups covering {3 * len(tasks)} Winogender sentences.")


if __name__ == "__main__":
    main()
