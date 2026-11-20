"""BLiMP's prompt and grader for Benchopedia runs.

runner/run.py sends messages(task) to the model ATTEMPTS times per task and
grades each final output with grade(task, output). scripts/check_evals.py
checks that grade() accepts every reference solution.

BLiMP's paper scores a language model as correct on a pair when it assigns the
acceptable sentence a higher probability, and its human validators chose the
acceptable sentence in a forced-choice task. A chat model cannot return
sentence probabilities through the runner, so this prompt asks for the forced
choice, and grade() checks that the chosen sentence is the acceptable one.
"""

import re

# Two sentences: guessing passes five attempts one time in 32.
ATTEMPTS = 5

INSTRUCTION = ('End your response with a final line of the form "Answer: <number>", '
               'where <number> is 1 or 2.')

# The final line's number, as in "Answer: 2", "**Answer:** 2" or the
# reference solution's "2. <sentence>".
CHOICE_RE = re.compile(r"^\W*(?:answer\W*)?([12])\b", re.IGNORECASE)


def messages(task):
    """The question and the two sentences, then the answer format."""
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def extract_choice(text):
    """The sentence number on the last non-empty line, or None."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    match = CHOICE_RE.match(lines[-1])
    return match.group(1) if match else None


def grade(task, output):
    """Returns (verdict, answer): answer is "1" or "2", or None when no choice can be read."""
    reference = extract_choice(task["solution"])
    assert reference is not None, f"{task['key']}: reference solution names no sentence"
    answer = extract_choice(output)
    if answer is None:
        return "unparseable", None
    return ("pass" if answer == reference else "fail"), answer
