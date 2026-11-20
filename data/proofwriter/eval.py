"""ProofWriter's prompt and grader for Benchopedia runs.

runner/run.py sends messages(task) to the model ATTEMPTS times per task and
grades each final output with grade(task, output). scripts/check_evals.py
checks that grade() accepts every reference solution.

ProofWriter's paper reports answer accuracy: the fraction of questions whose
True, False, or Unknown answer matches the label. grade() applies that rule to
one answer; it does not check proofs. This prompt asks for the answer on a
final line, so the model can reason first. A reply without that line is still
read when its first line is just the answer, as in the reference solutions.
"""

import re

# Three answers: guessing passes three attempts one time in 27.
ATTEMPTS = 3

INSTRUCTION = ('End your response with a final line of the form "Answer: <answer>", '
               'where <answer> is True, False, or Unknown.')

# The final line's answer, as in "Answer: True", "**Answer:** unknown" or "Answer: \"False\"".
ANSWER_RE = re.compile(r"^\W*answer\W*(true|false|unknown)\b", re.IGNORECASE)
# A first line that is only the answer, as in the reference solutions.
BARE_RE = re.compile(r"^\W*(true|false|unknown)\W*$", re.IGNORECASE)


def messages(task):
    """The question as published, then the answer format."""
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def extract_answer(output):
    """True, False or Unknown from the last non-empty line, else from a bare first line, or None."""
    lines = [line for line in output.splitlines() if line.strip()]
    if not lines:
        return None
    match = ANSWER_RE.match(lines[-1]) or BARE_RE.match(lines[0])
    return match.group(1).capitalize() if match else None


def grade(task, output):
    """Returns (verdict, answer): answer is "True", "False" or "Unknown", or None when none can be read."""
    reference = task["solution"].split("\n", 1)[0]
    assert reference in ("True", "False", "Unknown"), f"{task['key']}: reference solution does not start with an answer"
    answer = extract_answer(output)
    if answer is None:
        return "unparseable", None
    return ("pass" if answer == reference else "fail"), answer
