"""Score complete PCFG SET output sequences by exact token match."""

import re


ATTEMPTS = 2
MODEL_OPTIONS = {"reasoning": {"enabled": False}}
FENCE = re.compile(r"\x60{3}(?:text)?[ \t]*\n(.*?)\n\x60{3}", re.IGNORECASE | re.DOTALL)
SEQUENCE = re.compile(r"[A-Z][0-9]*(?:\s+[A-Z][0-9]*)*")
INSTRUCTIONS = (
    "Evaluate this prefix expression. Each operator comes before its arguments. "
    "A comma separates the two arguments of a binary operator. Evaluate nested expressions before using their results.\n\n"
    "Unary operators\n"
    "copy keeps the sequence. reverse reverses it. shift moves its first token to the end. "
    "echo adds another copy of its last token. swap_first_last exchanges its first and last tokens. "
    "repeat concatenates the sequence with itself.\n\n"
    "Binary operators\n"
    "append concatenates the first argument followed by the second. prepend puts the second argument before the first. "
    "remove_first keeps the second argument. remove_second keeps the first argument.\n\n"
    "Reply with only the resulting space-separated tokens."
)


def messages(task):
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTIONS}"}]


def grade(task, output):
    reply = output.strip()
    block = FENCE.fullmatch(reply)
    sequence = block[1].strip() if block else reply
    if not SEQUENCE.fullmatch(sequence):
        return "unparseable", None
    answer = " ".join(sequence.split())
    return ("pass" if answer == task["solution"] else "fail"), answer
