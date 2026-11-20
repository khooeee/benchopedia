"""Prompt and grader for copa.

COPA scores a prediction by whether it matches the labelled alternative.
"""

import re

ATTEMPTS = 5
INSTRUCTION = "Reply with only the number of the more plausible alternative (1 or 2)."
REFERENCE_RE = re.compile(r"Alternative ([12]):")
ANSWER_RE = re.compile(r"^\W*(?:answer\s*:\s*\W*)?([12])\W*$", re.IGNORECASE)


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
