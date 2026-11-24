"""Score the published binary consequence-plausibility label."""

import re


ATTEMPTS = 5
LABEL = re.compile(r"\W*(?:answer\s*:\s*\W*)?(plausible|implausible)\W*", re.IGNORECASE)


def messages(task):
    return [{"role": "user", "content": (
        f"{task['prompt']}\n\n"
        "Could the described consequence plausibly follow from the action? "
        "Reply with only plausible or implausible."
    )}]


def grade(task, output):
    lines = output.strip().splitlines()
    match = LABEL.fullmatch(lines[-1]) if lines else None
    if match is None:
        return "unparseable", None
    answer = match[1].lower()
    return ("pass" if answer == task["solution"] else "fail"), answer
