"""Prompt and grader for arc-challenge.

ARC-Challenge awards full credit for choosing the correct option.
"""

import re

ATTEMPTS = 3
INSTRUCTION = "Reply with only the option label shown in the question."
REFERENCE_RE = re.compile(r"([A-E1-4])\.")
ANSWER_RE = re.compile(r"^\W*(?:answer\s*:\s*\W*)?([A-E1-4])\W*$", re.IGNORECASE)
OPTION_RE = re.compile(r"^([A-E1-4])\. ", re.MULTILINE)


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
    choices = OPTION_RE.findall(task["prompt"])
    if answer not in choices:
        return "unparseable", None
    return ("pass" if answer == reference else "fail"), answer
