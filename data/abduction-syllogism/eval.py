"""Grade the choice number in the zero-shot syllogism evaluation."""

ATTEMPTS = 3
MODEL_OPTIONS = {"max_tokens": 10, "reasoning": {"enabled": False}}
CHOICES = {"1", "2", "3"}


def messages(task):
    return [{"role": "user", "content": task["prompt"] + "\n\nReply with only the number 1, 2, or 3."}]


def reference_output(task):
    return task["solution"].split(".", 1)[0]


def grade(task, output):
    choice = output.strip().removesuffix(".")
    if choice not in CHOICES:
        return "unparseable", None
    return ("pass" if choice == reference_output(task) else "fail"), choice
