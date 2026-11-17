"""Import all 11,873 SQuAD 2.0 development questions from a pinned SQuAD-explorer commit.

Run from the repository root: python3 data/squad-v2/import.py
Only Python's standard library is required.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "rajpurkar/SQuAD-explorer"
DATA_PATH = "dataset/dev-v2.0.json"
EXPECTED_ARTICLES = 35
EXPECTED_COUNT = 11873
EXPECTED_UNANSWERABLE = 5945


def fetch_dataset(revision):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{DATA_PATH}"
    with urllib.request.urlopen(url, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def check_spans(question_id, context, answers):
    for answer in answers:
        start, text = answer["answer_start"], answer["text"]
        if not text.strip() or context[start:start + len(text)] != text:
            raise ValueError(f"{question_id}: answer span does not match the passage")


def to_task(title, context, record, revision):
    question_id = record["id"]
    if not re.fullmatch(r"[0-9a-f]{24}", question_id) or not record["question"].strip():
        raise ValueError(f"{question_id}: unexpected ID or empty question")
    answers = record["answers"]
    plausible = record.get("plausible_answers", [])
    check_spans(question_id, context, answers + plausible)
    if record["is_impossible"]:
        if answers or len(plausible) > 1:
            raise ValueError(f"{question_id}: unanswerable question with answers")
        solution = "Unanswerable"
        if plausible:
            solution += f"\n\nPlausible but incorrect answer: {plausible[0]['text']}"
    else:
        if not answers or "plausible_answers" in record:
            raise ValueError(f"{question_id}: answerable question without answers")
        # Annotators often chose the same span; each distinct answer text is listed once.
        solution = "\n".join(dict.fromkeys(answer["text"] for answer in answers))
    source = f"https://github.com/{REPOSITORY}/blob/{revision}/{DATA_PATH}"
    return {
        "key": question_id,
        "prompt": f"{record['question']}\n\nWikipedia article: {title}\n\n{context}",
        "solution": solution,
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 11,873 SQuAD 2.0 development questions.")
    dataset = fetch_dataset(revision)
    if dataset.get("version") != "v2.0" or len(dataset["data"]) != EXPECTED_ARTICLES:
        sys.exit(f"Expected {EXPECTED_ARTICLES} articles in SQuAD v2.0 {DATA_PATH}.")
    tasks = []
    unanswerable = 0
    for article in dataset["data"]:
        for paragraph in article["paragraphs"]:
            for record in paragraph["qas"]:
                tasks.append(to_task(article["title"], paragraph["context"], record, revision))
                unanswerable += record["is_impossible"]
    if len(tasks) != EXPECTED_COUNT or unanswerable != EXPECTED_UNANSWERABLE:
        sys.exit(f"Expected {EXPECTED_COUNT} questions, {EXPECTED_UNANSWERABLE} unanswerable.")
    tasks.sort(key=lambda task: task["key"])
    if len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("SQuAD 2.0 question IDs are not unique.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} SQuAD 2.0 questions to {out}")


if __name__ == "__main__":
    main()
