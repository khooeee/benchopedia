"""Score the boolean, integer, or node-set answer to a basic GraphQA task."""

import re


ATTEMPTS = 5
BINARY_TASKS = {"cycle-check", "edge-existence"}
LIST_TASKS = {"connected-nodes", "disconnected-nodes"}
CYCLE_ANSWERS = {
    "yes, there is a cycle": "yes",
    "no, there is no cycle": "no",
}
INTEGER = re.compile(r"[0-9]+")
NODE_IDS = re.compile(r"[0-9]+(?:\s*,\s*[0-9]+)*")


def task_kind(task):
    return task["key"].removeprefix("graphqa-").rsplit("-", 1)[0]


def messages(task):
    kind = task_kind(task)
    if kind in BINARY_TASKS:
        instruction = "Reply with Yes or No."
    elif kind in LIST_TASKS:
        instruction = "Reply with comma-separated node IDs, or No nodes for an empty list."
    else:
        instruction = "Reply with one integer."
    return [{"role": "user", "content": task["prompt"] + "\n\n" + instruction}]


def parse_answer(kind, output):
    answer = output.strip().lower().removesuffix(".")
    if kind in BINARY_TASKS:
        if kind == "cycle-check":
            answer = CYCLE_ANSWERS.get(answer, answer)
        return answer if answer in {"yes", "no"} else None
    if kind not in LIST_TASKS:
        return str(int(answer)) if INTEGER.fullmatch(answer) else None
    if answer in {"no nodes", "[]"}:
        return "no nodes"
    if answer.startswith("[") and answer.endswith("]"):
        answer = answer[1:-1].strip()
    if NODE_IDS.fullmatch(answer):
        return ", ".join(map(str, sorted(map(int, answer.split(",")))))
    return None


def grade(task, output):
    kind = task_kind(task)
    answer = parse_answer(kind, output)
    if answer is None:
        return "unparseable", None
    reference = parse_answer(kind, task["solution"])
    return ("pass" if answer == reference else "fail"), answer
