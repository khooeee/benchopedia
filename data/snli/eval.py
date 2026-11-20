"""Score SNLI 1.0 against the majority labels in the pinned test split.

The paper defines three-way classification accuracy. The archive's readme
omits pairs with no majority label from evaluation.
https://arxiv.org/abs/1508.05326v1
https://archive.nyu.edu/handle/2451/41728
"""

import re

ATTEMPTS = 3
LABELS = {"entailment", "contradiction", "neutral"}
NO_MAJORITY = "- (no majority label)"
INSTRUCTION = 'End with "Answer: <label>", using entailment, contradiction, or neutral.'
LABEL_RE = re.compile(
    r"[*_]*(?:answer\s*:[*_]*\s*)?[*_]*(entailment|contradiction|neutral)[*_]*\.?",
    re.IGNORECASE,
)


def gold_label(task):
    return task["solution"].partition("\n")[0]


def is_eligible(task):
    """The archive excludes pairs whose annotators did not reach a majority."""
    return gold_label(task) != NO_MAJORITY


def messages(task):
    if not is_eligible(task):
        raise ValueError(f"{task['key']}: SNLI excludes pairs with no majority label")
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def grade(task, output):
    reference = gold_label(task)
    if reference not in LABELS:
        raise ValueError(f"{task['key']}: expected one of the three SNLI gold labels")
    # Reference solutions also contain annotator labels below the gold label.
    if output == task["solution"]:
        output = reference
    lines = [line.strip() for line in output.splitlines() if line.strip()]
    match = LABEL_RE.fullmatch(lines[-1]) if lines else None
    if not match:
        return "unparseable", None
    answer = match.group(1).lower()
    return ("pass" if answer == reference else "fail"), answer
