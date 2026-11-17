"""Import all eleven MGSM language files from their pinned GitHub commit.

Run from the repository root: python3 data/mgsm/import.py
Only Python's standard library is required.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "google-research/url-nlp"
LANGUAGES = ("bn", "de", "en", "es", "fr", "ja", "ru", "sw", "te", "th", "zh")
PROBLEMS_PER_LANGUAGE = 250
EXPECTED_COUNT = PROBLEMS_PER_LANGUAGE * len(LANGUAGES)
ANSWER = re.compile(r"[0-9]{1,3}(,[0-9]{3})+|[0-9]+")


def source_path(language):
    return f"mgsm/mgsm_{language}.tsv"


def fetch_rows(revision, language):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{source_path(language)}"
    with urllib.request.urlopen(url, timeout=60) as response:
        text = response.read().decode("utf-8")
    if "\r" in text or not text.endswith("\n"):
        raise ValueError(f"{language}: unexpected line endings")
    # Split on line feeds only; Unicode line separators may occur inside text.
    return [line.split("\t") for line in text[:-1].split("\n")]


def to_task(language, line, fields, revision):
    where = f"{language} line {line}"
    if len(fields) != 2:
        raise ValueError(f"{where}: expected a question and an answer")
    question, answer = fields
    if not question.strip():
        raise ValueError(f"{where}: missing question")
    if not ANSWER.fullmatch(answer):
        raise ValueError(f"{where}: answer {answer!r} is not a whole number")
    source = (f"https://github.com/{REPOSITORY}/blob/{revision}/"
              f"{source_path(language)}?plain=1#L{line}")
    return {
        "key": f"{language}-{line:03d}",
        "prompt": question,
        "solution": answer,
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 250 problems in all eleven languages.")
    tasks, answers = [], {}
    for language in LANGUAGES:
        rows = fetch_rows(revision, language)
        if len(rows) != PROBLEMS_PER_LANGUAGE:
            sys.exit(f"{language}: expected {PROBLEMS_PER_LANGUAGE} rows, found {len(rows)}.")
        for line, fields in enumerate(rows, start=1):
            task = to_task(language, line, fields, revision)
            # Every language translates the same problem on the same line.
            if answers.setdefault(line, task["solution"]) != task["solution"]:
                sys.exit(f"{language} line {line}: answer differs from other languages.")
            tasks.append(task)
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("MGSM count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} MGSM tasks to {out}")


if __name__ == "__main__":
    main()
