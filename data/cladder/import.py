"""Import CLadder's main benchmark: the 10,112 questions of the balanced set.

Run from the repository root: python3 data/cladder/import.py
Only Python's standard library is required. The dataset archive is fetched from
the CLadder repository at the commit pinned in benchmark.json and checked against
its SHA-256 digest, so a rerun reproduces the same snapshot.
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
REPOSITORY = "causalNLP/cladder"
ARCHIVE = "data/cladder-v1.zip"
ARCHIVE_SHA256 = "9fdae052b1ebe4ee6a19fdfb3e1eb88a381c7345df394cea524bcce97e2349b3"
QUESTIONS = "cladder-v1-q-balanced.json"
MODELS = "cladder-v1-meta-models.json"
EXPECTED = 10112
# Backdoor-adjustment questions are published without reasoning steps, and
# collider-bias questions with an empty data-gathering step.
WITHOUT_REASONING = {"backadj"}
EMPTY_STEPS = {("collider_bias", "step4")}


def fetch_archive(revision):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{ARCHIVE}"
    print(f"Reading {url}")
    with urllib.request.urlopen(url, timeout=300) as response:
        data = response.read()
    if hashlib.sha256(data).hexdigest() != ARCHIVE_SHA256:
        sys.exit(f"{ARCHIVE}: SHA-256 digest does not match the pinned archive.")
    return zipfile.ZipFile(io.BytesIO(data))


def text(value, where):
    if not isinstance(value, str) or not value.strip():
        sys.exit(f"{where}: missing text.")
    return value.strip()


def to_task(question, models, source):
    where = f"question {question.get('question_id')}"
    meta = question["meta"]
    if question["answer"] not in ("yes", "no"):
        sys.exit(f"{where}: unexpected answer {question['answer']!r}.")
    model = models.get(meta["model_id"])
    if model is None:
        sys.exit(f"{where}: unknown model {meta['model_id']}.")
    # The prompt the authors recommend and their evaluation assembles: the
    # model's background, the question's given information, then the question.
    parts = (text(model["background"], where), text(question["given_info"], where),
             text(question["question"], where))
    reasoning = question["reasoning"]
    if meta["query_type"] in WITHOUT_REASONING:
        if reasoning is not None:
            sys.exit(f"{where}: expected no reasoning steps.")
        solution = question["answer"]
    else:
        if not isinstance(reasoning, dict) or not reasoning:
            sys.exit(f"{where}: missing reasoning steps.")
        for name, step in reasoning.items():
            if not isinstance(step, str) or (not step.strip() and (meta["query_type"], name) not in EMPTY_STEPS):
                sys.exit(f"{where}: empty reasoning step {name}.")
        solution = question["answer"] + "\n\n" + "\n".join(reasoning.values())
    return {
        "key": str(question["question_id"]),
        "prompt": " ".join(parts),
        "solution": solution,
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be a full Git commit SHA.")
    if benchmark["task_count"] != EXPECTED:
        sys.exit(f"The declared scope must be all {EXPECTED:,} balanced questions.")
    archive = fetch_archive(revision)
    questions = json.loads(archive.read(QUESTIONS).decode("utf-8"))
    models = {model["model_id"]: model for model in json.loads(archive.read(MODELS).decode("utf-8"))}
    if len(questions) != EXPECTED:
        sys.exit(f"{QUESTIONS}: expected {EXPECTED:,} questions, found {len(questions):,}.")
    if len({question["question_id"] for question in questions}) != EXPECTED:
        sys.exit(f"{QUESTIONS}: question IDs are not unique.")
    answers = Counter(question["answer"] for question in questions)
    if answers["yes"] != answers["no"]:
        sys.exit(f"{QUESTIONS}: answers are not balanced: {dict(answers)}.")
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{ARCHIVE}"
    tasks = [to_task(question, models, source)
             for question in sorted(questions, key=lambda question: question["question_id"])]
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} CLadder questions to {out}")


if __name__ == "__main__":
    main()
