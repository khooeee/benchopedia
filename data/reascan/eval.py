"""Prompt for actions and score ReaSCAN's exact sequence match."""

ATTEMPTS = 2
ACTIONS = {"walk", "push", "pull", "turn left", "turn right", "stay"}
INSTRUCTION = (
    "Rows increase south and columns increase east. The position of a box is its upper-left corner. "
    "Walk to the described object's cell, even when another object is on the route. "
    "Move along columns first and then rows. For zigzagging, alternate a column step and a row step "
    "toward the goal, starting with a column step. Once aligned with the goal, walk straight. "
    "Turn to face a walking step, using two left turns for a half turn. "
    "After reaching the object, push in your facing direction or pull in the opposite direction "
    "without turning. Move it until the next cell is outside the grid or occupied. A box by itself "
    "allows entry. Moving a size-1 or size-2 object one cell takes one push or pull, and sizes 3 "
    "and 4 take two. For walking, pushing, or pulling hesitantly, add stay after each action. "
    "For spinning, make four left turns before each action, before turning to a new walking direction. "
    "For cautious movement, face the walking direction first, then turn left, right, right, left "
    "before each walk, push, or pull. A pull retains the agent's facing.\n\n"
    "Return only a comma-separated action sequence using walk, push, pull, turn left, turn right, or stay."
)


def messages(task):
    return [{"role": "user", "content": task["prompt"] + "\n\n" + INSTRUCTION}]


def parse_actions(output):
    answer = output.strip().lower().removesuffix(".")
    parts = answer.split(",") if "," in answer else answer.splitlines()
    steps = [" ".join(step.split()) for step in parts]
    return steps if steps and set(steps) <= ACTIONS else None


def grade(task, output):
    steps = parse_actions(output)
    if steps is None:
        return "unparseable", None
    answer = ",".join(steps)
    return ("pass" if answer == task["solution"] else "fail"), answer
