"""Score the two HANS entailment labels."""

import re


ATTEMPTS = 5
LABEL = re.compile(
    r"\W*(?:answer\s*:\s*\W*)?(entailment|non[- ]entailment|neutral|contradiction)\W*",
    re.IGNORECASE,
)


def messages(task):
    return [{"role": "user", "content": (
        f"{task['prompt']}\n\n"
        "Decide whether the hypothesis must be true if the premise is true. "
        "Reply with only entailment or non-entailment."
    )}]


def grade(task, output):
    lines = output.strip().splitlines()
    match = LABEL.fullmatch(lines[-1]) if lines else None
    if match is None:
        return "unparseable", None
    # HANS collapses the valid MNLI labels neutral and contradiction.
    answer = "entailment" if match[1].lower() == "entailment" else "non-entailment"
    return ("pass" if answer == task["solution"] else "fail"), answer
