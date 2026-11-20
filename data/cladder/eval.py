"""CLadder's prompt and grader for Benchopedia runs.

runner/run.py sends messages(task) to the model ATTEMPTS times per task and
grades each final output with grade(task, output). scripts/check_evals.py
checks that grade() accepts every reference solution.

CLadder's paper reports accuracy: the fraction of questions whose yes-or-no
answer matches the label. grade() applies that rule to one answer. This prompt
asks for the answer on a final line, so the model can reason first. A reply
without that line is still read when its first line is just yes or no, as in
the reference solutions; the authors' script reads the answer from the start
of the reply.
"""

import re

# Two answers: guessing passes five attempts one time in 32.
ATTEMPTS = 5

INSTRUCTION = ('Answer the question. End your response with a final line of the form '
               '"Answer: <answer>", where <answer> is yes or no.')

# The final line's answer, as in "Answer: yes", "**Answer:** No" or "Answer: \"yes\"".
ANSWER_RE = re.compile(r"^\W*answer\W*(yes|no)\b", re.IGNORECASE)
# A first line that is only the answer, as in the reference solutions.
BARE_RE = re.compile(r"^\W*(yes|no)\W*$", re.IGNORECASE)


def messages(task):
    """The question as published, then the answer format."""
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def extract_answer(output):
    """yes or no from the last non-empty line, else from a bare first line, or None."""
    lines = [line for line in output.splitlines() if line.strip()]
    if not lines:
        return None
    match = ANSWER_RE.match(lines[-1]) or BARE_RE.match(lines[0])
    return match.group(1).lower() if match else None


def grade(task, output):
    """Returns (verdict, answer): answer is "yes" or "no", or None when none can be read."""
    reference = task["solution"].split("\n", 1)[0]
    assert reference in ("yes", "no"), f"{task['key']}: reference solution does not start with yes or no"
    answer = extract_answer(output)
    if answer is None:
        return "unparseable", None
    return ("pass" if answer == reference else "fail"), answer
