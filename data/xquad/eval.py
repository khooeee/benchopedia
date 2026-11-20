"""XQuAD's SQuAD v1.1 exact-match rule for Benchopedia's solve verdict.

The pinned XQuAD README specifies the official SQuAD v1.1 evaluation.
https://github.com/google-deepmind/xquad/blob/7d30520c717524000f0d9d2f9c10a069acd9d285/README.md#training-and-evaluation
"""

import re
import string

ATTEMPTS = 2
INSTRUCTION = "Copy the shortest span that answers the question from the passage. Reply with only that text."
ASCII_PUNCTUATION = str.maketrans("", "", string.punctuation)
ENGLISH_ARTICLES = re.compile(r"\b(?:a|an|the)\b")


def normalize_span(text):
    text = text.lower().translate(ASCII_PUNCTUATION)
    return " ".join(ENGLISH_ARTICLES.sub(" ", text).split())


def messages(task):
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def grade(task, output):
    answer = output.strip()
    if not answer:
        return "unparseable", None
    correct = normalize_span(answer) == normalize_span(task["solution"])
    return ("pass" if correct else "fail"), answer
