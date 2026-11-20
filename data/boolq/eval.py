"""Prompt and grader for boolq.

BoolQ scores a prediction by whether it matches the yes-or-no label.
"""

import re

ATTEMPTS = 5
INSTRUCTION = "Reply with only the word yes or no."
REFERENCE_RE = re.compile(r"(yes|no)$")
ANSWER_RE = re.compile(r"^\W*(?:answer\s*:\s*\W*)?(yes|no)\W*$", re.IGNORECASE)


def messages(task):
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def grade(task, output):
    reference = REFERENCE_RE.match(task["solution"]).group(1)
    if output.strip() == task["solution"].strip():
        return "pass", reference
    lines = output.strip().splitlines()
    match = ANSWER_RE.fullmatch(lines[-1]) if lines else None
    if match is None:
        return "unparseable", None
    answer = match.group(1).lower()
    return ("pass" if answer == reference else "fail"), answer
