"""PopQA's prompt and grader for Benchopedia runs.

runner/run.py sends messages(task) to the model ATTEMPTS times per task and
grades each final output with grade(task, output). scripts/check_evals.py
checks that grade() accepts every reference solution.

The authors' run_model.py marks a prediction correct when any accepted answer,
as published, lowercased or capitalized, appears anywhere in it:
https://github.com/AlexTMallen/adaptive-retrieval/blob/8172ab04794a1651488207c230286b0b3786d736/run_model.py#L271-L276
Their prediction is a base model's first line of at most 15 tokens; a chat
model is asked to end with its answer on a line of its own, and the same test
is applied to that line.
"""

import re

# A wrong short answer is rarely right by chance, so two passing attempts are enough.
ATTEMPTS = 2

INSTRUCTION = ('Answer the question. End your response with a final line of the form "Answer: <answer>", '
               "where <answer> is just the answer, in as few words as possible.")

# The label on the final line, allowing Markdown emphasis such as **Answer:**.
LABEL_RE = re.compile(r"^[\s*_]*answer[\s*_]*:[\s*_]*", re.IGNORECASE)


def messages(task):
    """The question exactly as published, then the answer format."""
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def extract_answer(output):
    """The last non-empty line, without its "Answer:" label; None if the output is empty."""
    lines = [line for line in output.splitlines() if line.strip()]
    if not lines:
        return None
    return LABEL_RE.sub("", lines[-1]).strip() or None


def grade(task, output):
    """Grade as run_model.py does: some accepted answer must appear in the answer line.

    Returns (verdict, answer): verdict is "pass", "fail" or "unparseable", and
    answer is the final line's answer, or None when the output is empty.
    """
    pred = extract_answer(output)
    if pred is None:
        return "unparseable", None
    possible_answers = task["solution"].split("\n")
    is_correct = any(pa in pred or pa.lower() in pred or pa.capitalize() in pred for pa in possible_answers)
    return ("pass" if is_correct else "fail"), pred
