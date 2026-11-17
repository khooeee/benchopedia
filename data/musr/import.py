"""Import all 756 MuSR questions from the authors' pinned GitHub commit.

Run from the repository root: python3 data/musr/import.py
Only Python's standard library is required.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "Zayne-sprague/MuSR"
# Upstream file name, key prefix, and expected (stories, questions).
DOMAINS = {
    "murder_mystery": ("murder-mystery", 250, 250),
    "object_placements": ("object-placements", 64, 256),
    "team_allocation": ("team-allocation", 250, 250),
}
EXPECTED_COUNT = sum(questions for _, _, questions in DOMAINS.values())


def source_path(domain):
    return f"datasets/{domain}.json"


def fetch_stories(revision, domain):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{source_path(domain)}"
    with urllib.request.urlopen(url, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def to_task(domain, number, context, question, revision):
    prefix = DOMAINS[domain][0]
    where = f"{domain} question {number}"
    text, choices, answer = (question.get(field) for field in ("question", "choices", "answer"))
    if not isinstance(context, str) or not context.strip():
        raise ValueError(f"{where}: missing narrative")
    if not isinstance(text, str) or not text.strip():
        raise ValueError(f"{where}: missing question")
    if (not isinstance(choices, list) or len(choices) < 2
            or not all(isinstance(choice, str) and choice.strip() for choice in choices)):
        raise ValueError(f"{where}: missing choices")
    if not isinstance(answer, int) or not 0 <= answer < len(choices):
        raise ValueError(f"{where}: answer index outside the choices")
    # Number choices from 1, as the authors' evaluation prompt does.
    numbered = "\n".join(f"{index} - {choice}" for index, choice in enumerate(choices, start=1))
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{source_path(domain)}"
    return {
        "key": f"{prefix}-{number:03d}",
        "prompt": f"{context}\n\n{text}\n\n{numbered}",
        "solution": f"{answer + 1} - {choices[answer]}",
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 756 MuSR questions.")
    tasks = []
    for domain, (_, story_count, question_count) in DOMAINS.items():
        stories = fetch_stories(revision, domain)
        questions = [(story.get("context"), question)
                     for story in stories for question in story.get("questions", [])]
        if len(stories) != story_count or len(questions) != question_count:
            sys.exit(f"{domain}: expected {story_count} stories and {question_count} questions.")
        tasks.extend(to_task(domain, number, context, question, revision)
                     for number, (context, question) in enumerate(questions, start=1))
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("MuSR count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} MuSR questions to {out}")


if __name__ == "__main__":
    main()
