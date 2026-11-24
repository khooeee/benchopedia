"""Use the released direct whole-trace prompts and grade the first mistake."""

import json
from pathlib import Path
import re


ATTEMPTS = 2
CAPTURE_FILES = ("direct-prompts.json",)
DIRECT_PROMPTS = json.loads(Path(__file__).with_name(CAPTURE_FILES[0]).read_text(encoding="utf-8"))["conditions"]
LABEL = re.compile(r"no|[1-9][0-9]*", re.IGNORECASE)


def messages(task):
    family = task["key"].rsplit("-", 1)[0]
    examples = DIRECT_PROMPTS[family]["messages"]
    return [example.copy() for example in examples] + [{"role": "user", "content": task["prompt"]}]


def grade(task, output):
    answer = output.strip().removesuffix(".")
    if LABEL.fullmatch(answer) is None:
        return "unparseable", None
    answer = "No" if answer.lower() == "no" else answer
    return ("pass" if answer == task["solution"] else "fail"), answer
