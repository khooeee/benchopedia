"""Score HotpotQA distractor development answers and supporting facts.

Implements the 12 metrics defined by the pinned upstream scorer. Input facts
use the original zero-based indices, reconstructed from the pinned split.
https://github.com/hotpotqa/hotpot/blob/3635853403a8735609ee997664e1528f4480762a/hotpot_evaluate_v1.py
"""

from collections import Counter
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import string


ATTEMPTS = 1
CAPTURE_FILES = ("sentence-boundaries.json",)
BOUNDARIES_SHA256 = "c164200a198e0ad0fb56807bce33dd70170d9dec336769f96e86cbf41c923349"
FACT_LINE = re.compile(r"^(.+) \(sentence ([0-9]+)\)(?:: .*)?$")
ARTICLES = re.compile(r"\b(a|an|the)\b")
PUNCTUATION = str.maketrans("", "", string.punctuation)
CATEGORICAL = {"yes", "no", "noanswer"}


@lru_cache(maxsize=1)
def boundaries():
    path = Path(__file__).with_name("sentence-boundaries.json")
    payload = path.read_bytes()
    if hashlib.sha256(payload).hexdigest() != BOUNDARIES_SHA256:
        raise ValueError(f"Unexpected revision of {path}")
    return json.loads(payload)


def paragraphs(task):
    question, *sections = task["prompt"].split("\n\n# ")
    offsets = boundaries()[task["key"]]
    if len(sections) != len(offsets):
        raise ValueError(f"{task['key']}: paragraph count differs from the pinned split")
    context = []
    for section, cuts in zip(sections, offsets):
        title, _, paragraph = section.partition("\n\n")
        ends = [0, *cuts, len(paragraph)]
        sentences = [paragraph[start:stop].strip() for start, stop in zip(ends, ends[1:])]
        context.append((title, sentences))
    return question, context


def messages(task):
    question, context = paragraphs(task)
    passages = ["\n".join([title] + [f"{i}: {sentence}" for i, sentence in enumerate(sentences)])
                for title, sentences in context]
    instruction = ('Reply with a JSON object containing "answer" (a short answer, yes or no) '
                   'and "sp" (a list of [exact title, zero-based sentence index] pairs '
                   'for the supporting facts).')
    return [{"role": "user", "content": "\n\n".join([question, *passages, instruction])}]


def references(task):
    answer, facts = task["solution"].split("\n\nSupporting sentences:\n", 1)
    pairs = []
    for fact in facts.split("\n"):
        match = FACT_LINE.fullmatch(fact)
        if match is None:
            raise ValueError(f"{task['key']}: invalid supporting sentence")
        pairs.append((match[1], int(match[2])))
    return answer, pairs


def normalize(text):
    return " ".join(ARTICLES.sub(" ", text.lower().translate(PUNCTUATION)).split())


def f1(precision, recall):
    return 2 * precision * recall / (precision + recall) if precision or recall else 0.0


def overlap(prediction, reference):
    shared = sum((Counter(prediction) & Counter(reference)).values())
    return shared / len(prediction) if prediction else 0.0, shared / len(reference) if reference else 0.0


def metrics(name, exact, precision, recall):
    return {name + "em": int(exact), name + "f1": f1(precision, recall),
            name + "prec": precision, name + "recall": recall}


def score(task, output):
    try:
        prediction = json.loads(output)
    except json.JSONDecodeError:
        return None
    if not isinstance(prediction, dict):
        return None
    answer, evidence = prediction.get("answer"), prediction.get("sp")
    if not isinstance(answer, str) or not isinstance(evidence, list) or not all(
        isinstance(pair, list) and len(pair) == 2 and isinstance(pair[0], str) and type(pair[1]) is int
        for pair in evidence
    ):
        return None
    gold_answer, gold_evidence = references(task)
    answer, gold_answer = normalize(answer), normalize(gold_answer)
    answer_exact = answer == gold_answer
    if not answer_exact and (answer in CATEGORICAL or gold_answer in CATEGORICAL):
        answer_precision, answer_recall = 0.0, 0.0
    else:
        answer_precision, answer_recall = overlap(answer.split(), gold_answer.split())
    evidence, gold_evidence = set(map(tuple, evidence)), set(gold_evidence)
    evidence_exact = evidence == gold_evidence
    evidence_precision, evidence_recall = overlap(evidence, gold_evidence)
    return (metrics("", answer_exact, answer_precision, answer_recall)
            | metrics("sp_", evidence_exact, evidence_precision, evidence_recall)
            | metrics("joint_", answer_exact and evidence_exact,
                      answer_precision * evidence_precision, answer_recall * evidence_recall))


def reference_output(task):
    answer, evidence = references(task)
    return json.dumps({"answer": answer, "sp": evidence}, ensure_ascii=False)
