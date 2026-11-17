"""Import all 14,280 XQuAD question-answer pairs from a pinned DeepMind commit.

Run from the repository root: python3 data/xquad/import.py
Only Python's standard library is required.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "google-deepmind/xquad"
# Language code and the name used in the repository README, in its order.
LANGUAGES = {"ar": "Arabic", "de": "German", "el": "Greek", "en": "English",
             "es": "Spanish", "hi": "Hindi", "ru": "Russian", "th": "Thai",
             "tr": "Turkish", "vi": "Vietnamese", "zh": "Chinese",
             "ro": "Romanian"}
# Every file holds the same parallel set: 5 paragraphs from each of 48 articles.
EXPECTED_ARTICLES = 48
EXPECTED_PARAGRAPHS = 240
EXPECTED_PER_LANGUAGE = 1190
EXPECTED_COUNT = EXPECTED_PER_LANGUAGE * len(LANGUAGES)


def fetch(revision, language):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/xquad.{language}.json"
    with urllib.request.urlopen(url, timeout=120) as response:
        return json.loads(response.read().decode("utf-8"))


def to_task(language, title, context, record, source):
    question_id = record["id"]
    if not re.fullmatch(r"[0-9a-f]{24}", question_id):
        raise ValueError(f"{question_id}: unexpected upstream question ID")
    if not record["question"].strip() or not title.strip() or not context.strip():
        raise ValueError(f"{question_id}: empty question, article title, or paragraph")
    answers = record["answers"]
    if len(answers) != 1:
        raise ValueError(f"{question_id}: expected one reference answer")
    start, text = answers[0]["answer_start"], answers[0]["text"]
    # Translators kept the answer marked inside the paragraph, so the span holds
    # in every language; a mismatch means the file is not the pinned snapshot.
    if not text.strip() or context[start:start + len(text)] != text:
        raise ValueError(f"{question_id}: answer span does not match the paragraph")
    return {
        "key": f"{language}-{question_id}",
        "prompt": f"{record['question']}\n\nWikipedia article: {title}\n\n{context}",
        "solution": text,
        "prompt_source_url": source,
        "solution_source_url": source,
    }


def language_tasks(revision, language):
    dataset = fetch(revision, language)
    if dataset.get("version") != "1.1" or len(dataset["data"]) != EXPECTED_ARTICLES:
        sys.exit(f"xquad.{language}.json: expected {EXPECTED_ARTICLES} SQuAD v1.1 articles.")
    source = (f"https://github.com/{REPOSITORY}/blob/{revision}/xquad.{language}.json")
    tasks, paragraphs = [], 0
    for article in dataset["data"]:
        for paragraph in article["paragraphs"]:
            paragraphs += 1
            for record in paragraph["qas"]:
                tasks.append(to_task(language, article["title"],
                                     paragraph["context"], record, source))
    if paragraphs != EXPECTED_PARAGRAPHS or len(tasks) != EXPECTED_PER_LANGUAGE:
        sys.exit(f"xquad.{language}.json: expected {EXPECTED_PARAGRAPHS} paragraphs "
                 f"and {EXPECTED_PER_LANGUAGE} questions, found {paragraphs} and {len(tasks)}.")
    return tasks


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit(f"The declared scope must be all {EXPECTED_COUNT} XQuAD question-answer pairs.")
    tasks = [task for language in LANGUAGES for task in language_tasks(revision, language)]
    # The files are parallel, so every language must carry the same question IDs.
    per_language = {language: {task["key"].split("-", 1)[1] for task in tasks
                               if task["key"].startswith(f"{language}-")}
                    for language in LANGUAGES}
    if len(set(map(frozenset, per_language.values()))) != 1:
        sys.exit("XQuAD language files do not hold the same question IDs.")
    tasks.sort(key=lambda task: task["key"])
    if len(tasks) != EXPECTED_COUNT or len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("XQuAD count or identifiers differ from the declared scope.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} XQuAD question-answer pairs "
          f"in {len(LANGUAGES)} languages to {out}")


if __name__ == "__main__":
    main()
