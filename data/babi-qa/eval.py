"""Grade answer labels as in Facebook's MemN2N test protocol."""

import re


# The yes/no categories have two possible labels.
ATTEMPTS = 5
ANSWER = re.compile(r"[a-z0-9'-]+(?:\s*,\s*[a-z0-9'-]+)*")
INSTRUCTION = "Reply with just the answer label. Separate multiple answer parts with commas."


def messages(task):
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def grade(task, output):
    response = output.strip().lower().removesuffix(".")
    answer = ",".join(part.strip().removeprefix("the ") for part in response.split(","))
    if not ANSWER.fullmatch(answer):
        return "unparseable", None
    expected = task["solution"].lower()
    return ("pass" if answer == expected else "fail"), answer
