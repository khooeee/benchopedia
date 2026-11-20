"""Import ProofWriter's open-world depth-5 test set: 20,030 questions on 948 theories.

Run from the repository root: python3 data/proofwriter/import.py
Only Python's standard library is required. The versioned dataset archive is
fetched from AI2's public bucket and checked against the SHA-256 digest pinned in
benchmark.json, so a rerun reproduces the same snapshot.
"""

import hashlib
import io
import json
import re
import sys
import urllib.request
import zipfile
from collections import Counter
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
ARCHIVE_URL = "https://aristo-data-public.s3.amazonaws.com/proofwriter/proofwriter-dataset-V2020.12.3.zip"
SPLIT = "proofwriter-dataset-V2020.12.3/OWA/depth-5/meta-test.jsonl"
EXPECTED_THEORIES = 948
EXPECTED = 20030
INSTRUCTION = ("Using only the facts and rules above, is the statement true, false, or unknown? "
               "It is true if it follows from them, false if its negation follows from them, "
               "and unknown if neither does.")
# How each answer was derived, per the archive's README: proved, negation
# proved, or neither (an unproved rule conclusion or a random statement).
STRATEGIES = {
    True: {"proof"},
    False: {"inv-proof"},
    "Unknown": {"rconc", "inv-rconc", "random", "inv-random"},
}
LABELS = {True: "True", False: "False", "Unknown": "Unknown"}
REFERENCE = re.compile(r"\b(triple|rule)(\d+)\b")


def fetch_archive(digest):
    print(f"Reading {ARCHIVE_URL}")
    with urllib.request.urlopen(ARCHIVE_URL, timeout=600) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != digest:
        sys.exit("The archive's SHA-256 digest does not match dataset_revision.")
    return zipfile.ZipFile(io.BytesIO(data))


def legend(theory, proofs, where):
    """One line per fact and rule the proofs cite, facts first, in numeric order."""
    cited = sorted({(kind, int(number)) for kind, number in REFERENCE.findall(proofs)},
                   key=lambda item: (item[0] != "triple", item[1]))
    if not cited:
        sys.exit(f"{where}: proof cites no facts or rules.")
    lines = []
    for kind, number in cited:
        entry = theory["triples" if kind == "triple" else "rules"].get(f"{kind}{number}")
        if entry is None:
            sys.exit(f"{where}: proof cites missing {kind}{number}.")
        lines.append(f"{kind}{number}: {entry['text']}")
    return "\n".join(lines)


def to_task(theory, name, question, source):
    where = f"{theory['id']} {name}"
    answer = question["answer"]
    if answer not in STRATEGIES or question["strategy"] not in STRATEGIES[answer]:
        sys.exit(f"{where}: unexpected answer {answer!r} with strategy {question['strategy']!r}.")
    statement = question["question"]
    if not statement.strip() or statement != statement.strip():
        sys.exit(f"{where}: unexpected statement text.")
    solution = LABELS[answer]
    if answer != "Unknown":
        proofs = question["proofs"]
        if not proofs.startswith("[(") or not proofs.endswith(")]"):
            sys.exit(f"{where}: unexpected proof {proofs[:40]!r}.")
        heading = "Proof" if answer is True else "Proof of the negation"
        solution += f"\n\n{heading}: {proofs}\n{legend(theory, proofs, where)}"
    return {
        "key": f"{theory['id']}-{name}",
        "prompt": f"{theory['theory']}\n\nStatement: {statement}\n\n{INSTRUCTION}",
        "solution": solution,
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    digest = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{64}", digest):
        sys.exit("dataset_revision must be the archive's SHA-256 digest.")
    if benchmark["task_count"] != EXPECTED:
        sys.exit(f"The declared scope must be all {EXPECTED:,} questions.")
    archive = fetch_archive(digest)
    lines = archive.read(SPLIT).decode("utf-8").splitlines()
    theories = [json.loads(line) for line in lines if line.strip()]
    if len(theories) != EXPECTED_THEORIES:
        sys.exit(f"{SPLIT}: expected {EXPECTED_THEORIES} theories, found {len(theories)}.")
    tasks = []
    for theory in theories:
        # Facts are numbered triple1, triple2, ... and rules rule1, rule2, ...
        # in the order the theory states them, so proofs can be read against it.
        sentences = [theory["triples"][f"triple{n}"]["text"] for n in range(1, len(theory["triples"]) + 1)]
        sentences += [theory["rules"][f"rule{n}"]["text"] for n in range(1, len(theory["rules"]) + 1)]
        if theory["theory"] != " ".join(sentences):
            sys.exit(f"{theory['id']}: theory text differs from its facts and rules.")
        names = sorted(theory["questions"], key=lambda name: int(name.removeprefix("Q")))
        if names != [f"Q{n}" for n in range(1, len(names) + 1)]:
            sys.exit(f"{theory['id']}: questions are not numbered Q1 to Q{len(names)}.")
        tasks += [to_task(theory, name, theory["questions"][name], ARCHIVE_URL) for name in names]
    if len(tasks) != EXPECTED:
        sys.exit(f"{SPLIT}: expected {EXPECTED:,} questions, found {len(tasks):,}.")
    if len({task["key"] for task in tasks}) != len(tasks):
        sys.exit(f"{SPLIT}: keys are not unique.")
    answers = Counter(task["solution"].split("\n", 1)[0] for task in tasks)
    if answers["True"] != answers["False"]:
        sys.exit(f"{SPLIT}: true and false answers are not balanced: {dict(answers)}.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} ProofWriter questions to {out}")


if __name__ == "__main__":
    main()
