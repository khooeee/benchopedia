"""Score an MBPP completion against the three official test assertions.

The published prompt uses MBPP examples 2, 3 and 4 before each test problem.
https://github.com/google-research/google-research/blob/bb18d9b0cb460fee1a080fa2eeb4109fe3805275/mbpp/README.md
"""

from functools import lru_cache
import importlib.util
import json
from pathlib import Path
import re


ATTEMPTS = 1
TIMEOUT = 10
CAPTURE_FILES = ("few-shot.json", "runner/python_sandbox.py")
HERE = Path(__file__).resolve().parent
FENCE = re.compile(r"(?m)^(`{3,})python\n(.*?)^\1$", re.DOTALL)
TESTS_HEADER = "\n\nYour code should pass these tests:\n\n"
SETUP_HEADER = "\n\nTest setup:\n\n"


@lru_cache(maxsize=1)
def sandbox():
    path = HERE.parents[1] / "runner/python_sandbox.py"
    spec = importlib.util.spec_from_file_location("mbpp_python_sandbox", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_setup():
    return sandbox().check_setup()


@lru_cache(maxsize=1)
def few_shot():
    return json.loads((HERE / "few-shot.json").read_text(encoding="utf-8"))


def fields(task):
    head, _, tests_and_extras = task["prompt"].partition(TESTS_HEADER)
    text, _, setup = head.partition(SETUP_HEADER)
    tests = FENCE.match(tests_and_extras)
    if tests is None:
        raise ValueError(f"{task['key']}: missing the three MBPP tests")
    setup_code = FENCE.fullmatch(setup)[2] if setup else ""
    return text, setup_code, tests[2].rstrip("\n")


def messages(task):
    text, _, tests = fields(task)
    prompt = (f"You are an expert Python programmer, and here is your task: {text} "
              f"Your code should pass these tests:\n\n{tests}\n[BEGIN]\n")
    return [{"role": "user", "content": few_shot() + prompt}]


def grade(task, output):
    completion = output.partition("[DONE]")[0]
    if not completion.strip():
        return "unparseable", None
    _, setup, tests = fields(task)
    result = sandbox().execute("\n".join([setup, completion, tests]), TIMEOUT)
    return ("pass" if result == "passed" else "fail"), result
