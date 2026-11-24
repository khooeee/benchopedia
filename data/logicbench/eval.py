"""Score the final LogicBench BQA label under three zero-shot instructions."""

import re


ATTEMPTS = 1
INSTRUCTIONS = (
    "Use the stated context to work through the inference step by step.",
    "Think through the question in steps using the information in the context.",
    "Identify the rules stated in the narrative and apply them step by step to reach your conclusion.",
)
ANSWER_LINE = re.compile(r"(?:Answer:[ \t]*)?(yes|no)\.?", re.IGNORECASE)


def next_messages(task, outputs):
    if len(outputs) >= len(INSTRUCTIONS):
        return None
    instruction = INSTRUCTIONS[len(outputs)]
    content = (
        f"{task['prompt']}\n\n{instruction} Then give the final label on its own line, "
        "using Answer: Yes or Answer: No."
    )
    return [{"role": "user", "content": content}]


def label(output):
    lines = output.strip().splitlines()
    if not lines:
        return None
    match = ANSWER_LINE.fullmatch(lines[-1].strip())
    return match[1].lower() if match else None


def score_responses(task, outputs):
    if len(outputs) != len(INSTRUCTIONS):
        return None
    correct = sum(label(output) == task["solution"] for output in outputs)
    return {"accuracy": correct / len(outputs)}


def reference_responses(task):
    return [f"Answer: {task['solution'].capitalize()}"] * len(INSTRUCTIONS)
