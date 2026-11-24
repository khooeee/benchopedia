"""Score the answer-choice accuracy reported for QuaRTz."""

import re


ATTEMPTS = 5
ANSWER = re.compile(r"\W*(?:answer\s*:\s*\W*)?([AB])\W*", re.IGNORECASE)


def messages(task):
    return [{"role": "user", "content": (
        f"{task['prompt']}\n\nReply with only the option letter (A or B)."
    )}]


def grade(task, output):
    reference = task["solution"][0]
    reply = output.strip()
    if reply == task["solution"].strip():
        return "pass", reference
    lines = reply.splitlines()
    match = ANSWER.fullmatch(lines[-1]) if lines else None
    if match is None:
        return "unparseable", None
    answer = match[1].upper()
    return ("pass" if answer == reference else "fail"), answer
