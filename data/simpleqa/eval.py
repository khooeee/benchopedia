"""SimpleQA's pinned three-way LLM grading protocol."""

import json
import re
from functools import lru_cache
from pathlib import Path


ATTEMPTS = 1
JUDGE_MODEL = "gpt-4.1-2025-04-14"
CAPTURE_FILES = ("grader-prompt.json",)


@lru_cache(maxsize=1)
def grader_template():
    return json.loads(Path(__file__).with_name(CAPTURE_FILES[0]).read_text(encoding="utf-8"))


def next_messages(task, outputs):
    if not outputs:
        return [{"role": "user", "content": task["prompt"]}]
    if len(outputs) == 1:
        prompt = grader_template().format(
            question=task["prompt"], target=task["solution"], predicted_answer=outputs[0],
        )
        return [{"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}]


def score_responses(task, outputs):
    if len(outputs) != 2:
        return None
    match = re.search(r"(A|B|C)", outputs[1])
    grade = match.group(0) if match else "C"
    return {"is_correct": int(grade == "A"), "is_incorrect": int(grade == "B"),
            "is_not_attempted": int(grade == "C")}


def reference_responses(task):
    # Exercise the reference prompt and scoring offline with a fixed judge reply.
    return [task["solution"], "A"]
