"""Score the integer answer to an NLGraph maximum-flow problem."""

import re


ATTEMPTS = 2
INTEGER = re.compile(r"(?:answer\s*:\s*)?([0-9]+)\s*\.?", re.IGNORECASE)
QUESTION = re.compile(r"Q: What is the maximum flow from node ([0-9]+) to node ([0-9]+)\?")


def messages(task):
    return [{"role": "user", "content": (
        f"{task['prompt']}\n\nReply with only the maximum flow as a nonnegative integer."
    )}]


def grade(task, output):
    lines = output.strip().splitlines()
    if not lines:
        return "unparseable", None
    answer_line = lines[-1].strip().strip("*").strip()
    match = INTEGER.fullmatch(answer_line)
    if match is None and (question := QUESTION.search(task["prompt"])):
        source, sink = question.groups()
        match = re.fullmatch(
            rf"(?:the )?maximum flow from node {source} to node {sink} is ([0-9]+)(?:\s+units?)?\.?",
            answer_line,
            re.IGNORECASE,
        )
    if match is None:
        return "unparseable", None
    answer = match[1].lstrip("0") or "0"
    return ("pass" if answer == task["solution"] else "fail"), answer
