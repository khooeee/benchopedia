"""GSM8K's prompt and grader for Benchopedia runs.

runner/run.py sends messages(task) to the model ATTEMPTS times per task and
grades each final output with grade(task, output). scripts/check_evals.py
checks that grade() accepts every reference solution.

ANS_RE, INVALID_ANS and extract_answer are copied unchanged from the authors'
grade_school_math/dataset.py at the imported revision, which cannot be imported
directly because it loads torch:
https://github.com/openai/grade-school-math/blob/3101c7d5072418e28b9008a6636bde82a006892c/grade_school_math/dataset.py
"""

import re

# A wrong number is rarely right by chance, so two passing attempts are enough.
ATTEMPTS = 2

# The authors fine-tuned their models to end with "#### <number>"; chat models
# are asked to end the same way so the authors' extraction can read them.
INSTRUCTION = ('Solve the problem. End your response with a final line of the form "#### <answer>", '
               "where <answer> is just the final number, without units.")

ANS_RE = re.compile(r"#### (\-?[0-9\.\,]+)")
INVALID_ANS = "[invalid]"


def extract_answer(completion):
    match = ANS_RE.search(completion)
    if match:
        match_str = match.group(1).strip()
        match_str = match_str.replace(",", "")
        return match_str
    else:
        return INVALID_ANS


def messages(task):
    """The question exactly as published, then the answer format."""
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def grade(task, output):
    """Grade as the authors' is_correct does: the extracted strings must be equal.

    Returns (verdict, answer): verdict is "pass", "fail" or "unparseable", and
    answer is the extracted number, or None when the output has no "#### <number>".
    """
    reference = extract_answer(task["solution"])
    assert reference != INVALID_ANS, f"{task['key']}: reference solution has no final answer"
    answer = extract_answer(output)
    if answer == INVALID_ANS:
        return "unparseable", None
    return ("pass" if answer == reference else "fail"), answer
