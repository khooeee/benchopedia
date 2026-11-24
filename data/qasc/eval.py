"""Grade the released answer label for QASC's eight-choice questions."""

import re


ATTEMPTS = 3
ANSWER = re.compile(r"\W*(?:answer\s*:\s*\W*)?([A-H])\W*", re.IGNORECASE)


def messages(task):
    return [{"role": "user", "content": (
        f"{task['prompt']}\n\nReply with only the option letter (A through H)."
    )}]


def grade(task, output):
    reply = output.strip()
    reference = task["solution"][0]
    if reply == task["solution"].strip():
        return "pass", reference
    lines = reply.splitlines()
    match = ANSWER.fullmatch(lines[-1]) if lines else None
    if match is None:
        return "unparseable", None
    answer = match[1].upper()
    return ("pass" if answer == reference else "fail"), answer
