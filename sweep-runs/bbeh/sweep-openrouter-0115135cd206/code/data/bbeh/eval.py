# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

"""Score BBEH replies with the pinned upstream comparator.

The six scoring functions below are unchanged from the upstream evaluator:
https://github.com/google-deepmind/bbeh/blob/80d12ca916b7158f22293fcf3144f4d3d854d4be/bbeh/evaluate.py
Benchopedia adds the prompt, grade, and reference-check adapters and omits the
upstream module's example print calls.
"""


def strip_latex(response: str) -> str:
  if response.startswith("$") and response.endswith("$"):
    response = response[1:-1]
  if "boxed{" in response and response.endswith("}"):
    response = response[0:-1].split("boxed{")[1]
  if "text{" in response and response.endswith("}"):
    response = response[0:-1].split("text{")[1]
  if "texttt{" in response and response.endswith("}"):
    response = response[0:-1].split("texttt{")[1]
  return response


def extract_answer(sample: str) -> str:
  """Extracts the final answer from the sample."""
  answer_prefixes = [
      "The answer is:",
      "The final answer is ",
      "The final answer is: ",
      "The answer is "
  ]
  answer = sample
  for answer_prefix in answer_prefixes:
    if answer_prefix in answer:
      answer = answer.split(answer_prefix)[-1].strip()
  if answer.endswith("."):
    answer = answer[:-1]
  return strip_latex(answer)


def fuzzy_match(prediction: str, reference: str) -> bool:
  """Fuzzy match function for BigBench Extra Hard."""
  if prediction == reference:
    return True

  # (a) vs a
  if len(prediction) == 3 and prediction[0] == "(" and prediction[-1] == ")":
    return prediction[1] == reference
  if len(reference) == 3 and reference[0] == "(" and reference[-1] == ")":
    return reference[1] == prediction

  # Numbers
  try:
    if float(prediction) == float(reference):
      return True
  except ValueError:
    pass

  # quote issues
  if prediction.replace("'", "") == reference.replace("'", ""):
    return True

  # Bracket issues
  if f"[{reference}]" == prediction or f"[{prediction}]" == reference:
    return True

  # Question mark issues
  if prediction.endswith("?") and prediction[:-1] == reference:
    return True

  return False


def preprocess_sample(sample: str) -> str:
  prediction = extract_answer(sample.strip()).lower()
  prediction = prediction.replace(", ", ",").replace("**", "")
  prediction = prediction.split("\n")[0]
  prediction = prediction[0:-1] if prediction.endswith(".") else prediction
  return prediction


def preprocess_reference(reference: str) -> str:
  reference = reference.strip().lower()
  reference = reference.replace(", ", ",")
  return reference


def evaluate_correctness(sample: str, reference: str) -> bool:
  prediction = preprocess_sample(sample)
  reference = preprocess_reference(reference)
  return fuzzy_match(prediction, reference)


ATTEMPTS = 2

SUFFIX = (
    'Think step by step, and when you provide the final answer, please use the prefix "The answer is:" '
    "without any modification, and provide the answer directly, with no formatting, no bolding, and no "
    'markup. For instance: "The answer is: 42" or "The answer is: yes". If the question is multiple '
    "choice with a single correct answer, the final answer must only be the letter corresponding to the "
    'correct answer. For example, "The answer is: (a)".'
)


def messages(task):
    return [{"role": "user", "content": task["prompt"] + "\n\n" + SUFFIX}]


def grade(task, output):
    prediction = preprocess_sample(output)
    if not prediction:
        return "unparseable", None
    reference = preprocess_reference(task["solution"])
    return ("pass" if fuzzy_match(prediction, reference) else "fail"), prediction


def reference_output(task):
    target = task["solution"]
    output = f"The answer is: {target}"
    if target.endswith(".") and not evaluate_correctness(output, target):
        # The scorer drops a terminal period before ignoring single quotes.
        return f"The answer is: '{target}'"
    return output
