"""Grade answer labels as in Facebook's MemN2N test protocol."""

import re


# The yes/no categories have two possible labels.
ATTEMPTS = 5
ANSWER = re.compile(r"[a-z0-9'-]+(?:\s*,\s*[a-z0-9'-]+)*")
INSTRUCTION = "Reply with only the answer. Separate multiple answer parts with commas."


def messages(task):
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def grade(task, output):
    response = output.strip().lower()
    if not ANSWER.fullmatch(response):
        return "unparseable", None
    answer = ",".join(part.strip() for part in response.split(","))
    expected = task["solution"].lower()
    return ("pass" if answer == expected else "fail"), answer
