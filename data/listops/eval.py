"""Compare the generated digit with the original ListOps class label."""

import re


ATTEMPTS = 2


def is_eligible(task):
    expression = task["prompt"].rsplit("\n\n", 1)[1]
    return len(expression) > 1


def messages(task):
    return [{"role": "user", "content": task["prompt"] + "\n\nReply with one digit."}]


def grade(task, output):
    label = output.strip()
    if not re.fullmatch(r"[0-9]", label):
        return "unparseable", None
    return ("pass" if label == task["solution"] else "fail"), label
