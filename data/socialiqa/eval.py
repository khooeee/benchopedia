"""Prompt and grader for socialiqa.

SocialIQA scores a prediction by whether it matches the labelled option.
"""

import re

ATTEMPTS = 3
INSTRUCTION = "Reply with only the option letter (A, B, or C)."
REFERENCE_RE = re.compile(r"([A-C])\.")
ANSWER_RE = re.compile(r"^\W*(?:answer\s*:\s*\W*)?([A-C])\W*$", re.IGNORECASE)


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
    answer = match.group(1).upper()
    return ("pass" if answer == reference else "fail"), answer
