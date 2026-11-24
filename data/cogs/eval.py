"""Compare the ordered tokens of the returned COGS logical form."""

import re


ATTEMPTS = 2
TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]*|[0-9]+|[^\s]")
INSTRUCTION = (
    "Translate the sentence above into its COGS logical form. Index words from 0 "
    "and use x_<index> for noun and event heads. Use proper names directly as "
    "constants. Put starred definite noun predicates first, each followed by a "
    "semicolon. Join the other predicates with AND in head order. For roles "
    "of the same event, follow the word order of their arguments. Use COGS roles "
    "such as .agent, .theme, .recipient, .ccomp, .xcomp and .nmod.<preposition>.\n\n"
    "Example for \"A poet admired the fox .\"\n"
    "* fox ( x _ 4 ) ; poet ( x _ 1 ) AND admire . agent ( x _ 2 , x _ 1 ) "
    "AND admire . theme ( x _ 2 , x _ 4 )\n\n"
    "Return only the logical form."
)


def messages(task):
    return [{"role": "user", "content": task["prompt"] + "\n\n" + INSTRUCTION}]


def grade(task, output):
    tokens = TOKEN.findall(output)
    if not tokens:
        return "unparseable", None
    reference = TOKEN.findall(task["solution"])
    return ("pass" if tokens == reference else "fail"), " ".join(tokens)
