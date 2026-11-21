"""Question-level QuAC scores for one response and its two dialog acts.

Implements the published scorer's leave-one-out F1 and human agreement rules.
The reference script at https://s3.amazonaws.com/my89public/quac/scorer.py has
SHA-256 cd9a391bbc93a6e8c62dbbd0b4945d3f915850a9dd07be80a637d9dabff30f84.
"""

from collections import Counter
import json
import re
import string


ATTEMPTS = 1
MIN_HUMAN_F1 = 0.4
NO_ANSWER = "CANNOTANSWER"
YESNO = {"yes": "y", "no": "n", "neither": "x"}
FOLLOWUP = {"follow up": "y", "maybe follow up": "m", "don't follow up": "n"}
PUNCTUATION = str.maketrans("", "", string.punctuation)
ARTICLES = re.compile(r"\b(a|an|the)\b")
INSTRUCTION = (
    'Answer with a span from the section text, or CANNOTANSWER if it has no answer. '
    'Reply as a JSON object with "answer", "yesno" (y for yes, n for no, x for neither), '
    'and "followup" (y for follow up, m for maybe follow up, n for do not follow up).'
)


def messages(task):
    return [{"role": "user", "content": task["prompt"] + "\n\n" + INSTRUCTION}]


def references(task):
    spans, acts = task["solution"].rsplit("\n\n", 1)
    affirmation, continuation = acts.split("\n")
    return (spans.split("\n"), YESNO[affirmation.removeprefix("Affirmation: ")],
            FOLLOWUP[continuation.removeprefix("Continuation: ")])


def tokens(text):
    return Counter(ARTICLES.sub(" ", text.lower().translate(PUNCTUATION)).split())


def f1(prediction, reference):
    predicted = tokens(prediction)
    expected = tokens(reference)
    matches = sum((predicted & expected).values())
    if not matches:
        return 0.0
    precision = matches / sum(predicted.values())
    recall = matches / sum(expected.values())
    return 2 * precision * recall / (precision + recall)


def predictions_f1(answer, spans):
    if spans == [NO_ANSWER]:
        return float(answer == NO_ANSWER)
    overlaps = [f1(answer, span) for span in spans]
    if len(overlaps) == 1:
        return overlaps[0]
    return sum(max(overlaps[:i] + overlaps[i + 1:]) for i in range(len(overlaps))) / len(overlaps)


def agreement(spans):
    if len(spans) == 1:
        return 1.0
    return sum(max(f1(reference, other) for j, other in enumerate(spans) if i != j)
               for i, reference in enumerate(spans)) / len(spans)


def score(task, output):
    try:
        prediction = json.loads(output)
    except json.JSONDecodeError:
        return None
    if not isinstance(prediction, dict):
        return None
    answer = prediction.get("answer")
    yesno = prediction.get("yesno")
    followup = prediction.get("followup")
    if not isinstance(answer, str) or not answer.strip() or yesno not in ("y", "n", "x") or followup not in ("y", "m", "n"):
        return None
    spans, gold_yesno, gold_followup = references(task)
    answer_f1 = predictions_f1(answer, spans)
    human_f1 = agreement(spans)
    scores = {
        "unfiltered-f1": answer_f1,
        "human-f1": human_f1,
        "included-in-headline": int(human_f1 >= MIN_HUMAN_F1),
    }
    if human_f1 >= MIN_HUMAN_F1:
        scores.update({"f1": answer_f1, "heq-q": int(answer_f1 >= human_f1),
                       "yes-no-accuracy": int(yesno == gold_yesno),
                       "followup-accuracy": int(followup == gold_followup)})
        if spans == [NO_ANSWER]:
            scores["unanswerable-accuracy"] = answer_f1
    return scores


def reference_output(task):
    spans, yesno, followup = references(task)
    return json.dumps({"answer": spans[0], "yesno": yesno, "followup": followup}, ensure_ascii=False)
