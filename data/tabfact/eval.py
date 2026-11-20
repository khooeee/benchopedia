"""TabFact's prompt and grader for Benchopedia runs.

runner/run.py sends messages(task) to the model ATTEMPTS times per task and
grades each final output with grade(task, output). scripts/check_evals.py
checks that grade() accepts every reference solution.

TabFact is scored by accuracy: a prediction is correct when its label,
entailed or refuted, matches the statement's label. The authors' models output
the label directly; a chat model is asked to end with it on a line of its own.
"""

import re

# Two labels: guessing passes five attempts one time in 32.
ATTEMPTS = 5

INSTRUCTION = ('End your response with a final line of the form "Answer: <label>", '
               "where <label> is Entailed or Refuted.")

# The final line's label, as in "Answer: Refuted", "**Answer:** Entailed" or
# the reference solution's bare "Entailed".
LABEL_RE = re.compile(r"^\W*(?:answer\W*)?(entailed|refuted)\b", re.IGNORECASE)


def messages(task):
    """The table, the statement and the question, then the answer format."""
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def extract_label(text):
    """The label on the last non-empty line, capitalized, or None."""
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines:
        return None
    match = LABEL_RE.match(lines[-1])
    return match.group(1).capitalize() if match else None


def grade(task, output):
    """Returns (verdict, answer): answer is "Entailed" or "Refuted", or None when no label can be read."""
    reference = extract_label(task["solution"])
    assert reference is not None, f"{task['key']}: reference solution names no label"
    answer = extract_label(output)
    if answer is None:
        return "unparseable", None
    return ("pass" if answer == reference else "fail"), answer
