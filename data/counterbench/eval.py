"""Score the yes-or-no answer using CounterBench's standard accuracy metric."""

import re


ATTEMPTS = 5
MODEL_OPTIONS = {"temperature": 0}
INSTRUCTION = "Reply with one word, Yes or No."
ANSWER = re.compile(r"(yes|no)\.?", re.IGNORECASE)


def messages(task):
    return [{"role": "user", "content": task["prompt"] + "\n\n" + INSTRUCTION}]


def grade(task, output):
    match = ANSWER.fullmatch(output.strip())
    if match is None:
        return "unparseable", None
    answer = match.group(1).lower()
    return ("pass" if answer == task["solution"] else "fail"), answer
