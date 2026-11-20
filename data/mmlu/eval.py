"""Prompt and grader for mmlu.

This grades generated choices by answer accuracy. The original MMLU
protocol ranks letter probabilities after five same-subject examples.
"""

import re

ATTEMPTS = 3
INSTRUCTION = "Reply with only the option letter (A, B, C, or D)."
REFERENCE_RE = re.compile(r"([A-D])\.")
ANSWER_RE = re.compile(r"^\W*(?:answer\s*:\s*\W*)?([A-D])\W*$", re.IGNORECASE)


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
