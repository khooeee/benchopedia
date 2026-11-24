"""Compare the final CLRS-Text LCS traceback matrix with the released text."""

import re


ATTEMPTS = 2
MODEL_OPTIONS = {"reasoning": {"enabled": False}}
FENCE = re.compile(r"\x60{3}(?:text)?[ \t]*\n(.*?)\n\x60{3}", re.IGNORECASE | re.DOTALL)
CELL = r"(?:-1|[012])"
ROW = rf"\[\s*{CELL}(?:[\s,]+{CELL})*\s*\]"
MATRIX = re.compile(rf"\[\s*{ROW}(?:\s*,\s*{ROW})*\s*\]")
INSTRUCTIONS = (
    "Return only the final LCS traceback matrix b. The string vector labels the two sequences in key. "
    "Compute their longest common subsequence with dynamic programming. Use 0 for a matching pair "
    "and a diagonal step, 1 for an upward step, and 2 for a leftward step. "
    "When counts tie on an interior mismatch, choose up. On a first-column mismatch use 1. "
    "On a first-row mismatch use 2 when the first symbol of the first sequence matched an earlier "
    "symbol of the second sequence, and 1 otherwise.\n\n"
    "Match the dimensions of initial_trace, with one row and one column per entry in key. Place the "
    "traceback table in the upper-right block and fill the other cells with -1. Enclose each row in brackets, "
    "separate entries in a row by single spaces, and separate rows with comma and space. "
    "Use an outer pair of brackets around the matrix."
)


def messages(task):
    return [{"role": "user", "content": f"{task['prompt']}\n{INSTRUCTIONS}"}]


def grade(task, output):
    reply = output.strip()
    fenced = FENCE.fullmatch(reply)
    answer = (fenced[1] if fenced else reply).rsplit("|", 1)[-1].strip()
    answer = answer.removeprefix("b:").strip()
    if not MATRIX.fullmatch(answer):
        return "unparseable", None
    return ("pass" if answer == task["solution"] else "fail"), answer
