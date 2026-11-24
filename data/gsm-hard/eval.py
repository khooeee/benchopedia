"""Grade a numeric reply with PAL's absolute error threshold."""

import math
import re


ATTEMPTS = 2
NUMBER = re.compile(
    r"[+-]?(?:(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]*)?|\.[0-9]+)"
    r"(?:[eE][+-]?[0-9]+)?"
)


def messages(task):
    return [{"role": "user", "content": task["prompt"] + "\n\nUse the quantities as given. Reply with only the final number, including a minus sign if needed."}]


def grade(task, output):
    answer = output.strip()
    if not NUMBER.fullmatch(answer):
        return "unparseable", None
    answer = answer.replace(",", "")
    value = float(answer)
    if not math.isfinite(value):
        return "unparseable", None
    return ("pass" if abs(value - float(task["solution"])) < 1e-3 else "fail"), answer
