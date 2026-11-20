"""SQuAD 2.0's normalized exact-match rule for the sweep's solve verdict.

The pinned evaluator takes the best match across gold answer spans. It uses
the empty answer for impossible questions.
https://github.com/rajpurkar/SQuAD-explorer/blob/eee5fdbf62f8613a7812b03419e6b29617b74fd1/evaluate-v2.0.py
"""

import re
import string

ATTEMPTS = 2
ABSTAIN = "UNANSWERABLE"
INSTRUCTION = (
    "Copy the shortest span that answers the question from the passage. "
    f"Reply with only that text, or {ABSTAIN} if the passage does not answer the question."
)
PUNCTUATION = str.maketrans("", "", string.punctuation)
ARTICLES = re.compile(r"\b(?:a|an|the)\b")


def normalize_span(text):
    return " ".join(ARTICLES.sub(" ", text.lower().translate(PUNCTUATION)).split())


def references(task):
    solution = task["solution"]
    if solution == "Unanswerable" or solution.startswith("Unanswerable\n\n"):
        return []
    return [span for span in solution.split("\n") if normalize_span(span)]


def reference_output(task):
    spans = references(task)
    return spans[0] if spans else ABSTAIN


def messages(task):
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def grade(task, output):
    answer = output.strip()
    if not answer:
        return "unparseable", None
    if answer.upper() == ABSTAIN:
        answer = ""
    expected = {normalize_span(span) for span in references(task)} or {""}
    return ("pass" if normalize_span(answer) in expected else "fail"), answer
