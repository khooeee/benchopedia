"""Choose a published candidate and check whether it is the reference response."""

from pathlib import Path
import re


ATTEMPTS = 2
CAPTURE_FILES = ("candidates.txt",)
CANDIDATES = tuple(
    line.partition(" ")[2]
    for line in Path(__file__).with_name("candidates.txt").read_text(encoding="utf-8").splitlines()
)
CANDIDATE_IDS = {text: number for number, text in enumerate(CANDIDATES, 1)}
SYSTEM_PROMPT = (
    "Select the next bot response in a simulated restaurant-booking dialog. "
    "A customer line of <SILENCE> indicates an empty turn.\n\n"
    + "\n".join(f"{number}. {text}" for number, text in enumerate(CANDIDATES, 1))
)
SELECTION = re.compile(r"([0-9]{1,4})\.?")


def messages(task):
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task["prompt"] + "\n\nReply with just the candidate number."},
    ]


def reference_output(task):
    return str(CANDIDATE_IDS[task["solution"]])


def grade(task, output):
    label = output.strip()
    selection = SELECTION.fullmatch(label)
    if selection:
        number = int(selection.group(1))
        if not 1 <= number <= len(CANDIDATES):
            return "unparseable", None
        candidate = CANDIDATES[number - 1]
    elif label in CANDIDATE_IDS:
        candidate = label
    else:
        return "unparseable", None
    return ("pass" if candidate == task["solution"] else "fail"), candidate
