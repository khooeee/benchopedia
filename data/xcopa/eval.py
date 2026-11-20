"""XCOPA's prompt and grader for Benchopedia runs.

runner/run.py sends messages(task) to the model ATTEMPTS times per task and
grades each final output with grade(task, output). scripts/check_evals.py
checks that grade() accepts every reference solution.

XCOPA publishes no scorer; its paper reports accuracy, the fraction of
questions on which the chosen alternative is the labelled one. grade() applies
that rule to one answer.
"""

import re

# Two alternatives: guessing passes five attempts one time in 32.
ATTEMPTS = 5

INSTRUCTION = ('Choose the more plausible alternative. End your response with a final line of the form '
               '"Answer: <number>", where <number> is 1 or 2.')

# The final line's number, as in "Answer: 2", "**Answer:** Alternative 2" or
# the reference solution's "Alternative 2: ...".
CHOICE_RE = re.compile(r"^\W*(?:answer\W*)?(?:alternative\W*)?([12])\b", re.IGNORECASE)


def messages(task):
    """The premise, question and alternatives as published, then the answer format."""
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def extract_choice(text):
    """The alternative number on the last non-empty line, or None."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    match = CHOICE_RE.match(lines[-1])
    return match.group(1) if match else None


def grade(task, output):
    """Returns (verdict, answer): answer is "1" or "2", or None when no choice can be read."""
    reference = extract_choice(task["solution"])
    assert reference is not None, f"{task['key']}: reference solution names no alternative"
    answer = extract_choice(output)
    if answer is None:
        return "unparseable", None
    return ("pass" if answer == reference else "fail"), answer
