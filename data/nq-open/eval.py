"""NQ-Open's prompt and grader for Benchopedia runs.

runner/run.py sends messages(task) to the model ATTEMPTS times per task and
grades each final output with grade(task, output). scripts/check_evals.py
checks that grade() accepts every reference solution.

normalize_answer, exact_match_score and metric_max_over_ground_truths are
copied unchanged from ORQA's evaluation utilities, which cannot be imported
directly because the module loads TensorFlow:
https://github.com/google-research/language/blob/865fae65f63ef7e6b2989d4ff8b47f61750415a8/language/orqa/utils/eval_utils.py
Those three functions are Copyright 2018 The Google AI Language Team Authors
and licensed under the Apache License, Version 2.0; see LICENSE-language.
"""

import re
import string
import unicodedata

# A wrong short answer is rarely right by chance, so two passing attempts are enough.
ATTEMPTS = 2

# The official scorer compares one short answer string per question; chat
# models are asked to end with it on a line of its own so it can be read.
INSTRUCTION = ('Answer the question. End your response with a final line of the form "Answer: <answer>", '
               "where <answer> is just the answer, in as few words as possible.")

# The label on the final line, allowing Markdown emphasis such as **Answer:**.
LABEL_RE = re.compile(r"^[\s*_]*answer[\s*_]*:[\s*_]*", re.IGNORECASE)


def normalize_answer(s):
  """Normalize answer."""
  s = unicodedata.normalize("NFD", s)

  def remove_articles(text):
    return re.sub(r"\b(a|an|the)\b", " ", text)

  def white_space_fix(text):
    return " ".join(text.split())

  def remove_punc(text):
    exclude = set(string.punctuation)
    return "".join(ch for ch in text if ch not in exclude)

  def lower(text):
    return text.lower()

  return white_space_fix(remove_articles(remove_punc(lower(s))))


def exact_match_score(prediction, ground_truth):
  return normalize_answer(prediction) == normalize_answer(ground_truth)


def metric_max_over_ground_truths(metric_fn, prediction,
                                  ground_truths):
  scores_for_ground_truths = []
  for ground_truth in ground_truths:
    score = metric_fn(prediction, ground_truth)
    scores_for_ground_truths.append(score)
  return max(scores_for_ground_truths)


def messages(task):
    """The question exactly as published, then the answer format."""
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def extract_answer(output):
    """The last non-empty line, without its "Answer:" label; None if the output is empty."""
    lines = [line for line in output.splitlines() if line.strip()]
    if not lines:
        return None
    return LABEL_RE.sub("", lines[-1]).strip()


def grade(task, output):
    """Grade as ORQA's is_correct does without regexes: the answer must equal a reference after normalization.

    Returns (verdict, answer): verdict is "pass", "fail" or "unparseable", and
    answer is the extracted line, or None when the output is empty. The
    references are the solution's lines, one answer per line.
    """
    references = task["solution"].split("\n")
    answer = extract_answer(output)
    if answer is None:
        return "unparseable", None
    correct = metric_max_over_ground_truths(exact_match_score, answer, references)
    return ("pass" if correct else "fail"), answer
