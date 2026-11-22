"""Run CRUXEval-O and CRUXEval-I with the pinned direct prompts.

The prompt functions below retain the upstream MIT-licensed implementation.
https://github.com/facebookresearch/cruxeval/blob/190faf16d175b5847b0af05d937872b1fb395942/prompts.py
The response filters and assertions follow the upstream inference tasks and
evaluation/utils_general.py at the same revision.
"""

from functools import lru_cache
import importlib.util
from pathlib import Path


ATTEMPTS = 1
CAPTURE_FILES = ("runner/python_sandbox.py",)


@lru_cache(maxsize=1)
def sandbox():
    path = Path(__file__).resolve().parents[2] / "runner/python_sandbox.py"
    spec = importlib.util.spec_from_file_location("cruxeval_python_sandbox", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_setup():
    return sandbox().check_setup()


def fields(task):
    _, _, sections = task["prompt"].partition("~~~python\n")
    output_section, _, input_section = sections.partition("\n~~~")
    code, arguments = output_section.rsplit("\nassert f(", 1)
    _, _, output = input_section.rpartition("\nassert f(??) == ")
    return code, arguments.removesuffix(") == ??"), output.removesuffix("\n~~~")


def next_messages(task, outputs):
    code, arguments, truth = fields(task)
    if not outputs:
        prompt = make_direct_output_prompt((code, arguments))
    elif len(outputs) == 1:
        prompt = make_direct_input_prompt((code, truth))
    else:
        return None
    return [{"role": "user", "content": prompt}]


def response_text(output):
    return output.partition("[/ANSWER]")[0].removeprefix("[ANSWER]").strip()


def score_responses(task, outputs):
    code, arguments, truth = fields(task)
    output_reply, input_reply = map(response_text, outputs)
    output_guess = output_reply.split("==")[1].strip() if "==" in output_reply else output_reply
    input_guess = input_reply.split("==")[0].strip()
    if "assert f" in input_guess:
        input_guess = "f" + input_guess.split("assert f")[1].strip()

    output_score = 0
    if output_guess and f"f({arguments})" not in output_guess:
        output_score = int(sandbox().execute(f"{code}\nassert {truth} == {output_guess}", 3) == "passed")
    input_score = 0
    if "f(" in input_guess:
        input_score = int(sandbox().execute(f"{code}\nassert {truth} == {input_guess}", 3) == "passed")
    return {"pass-at-1-output": output_score, "pass-at-1-input": input_score}


def reference_responses(task):
    _, arguments, truth = fields(task)
    assertion = f"assert f({arguments}) == {truth}"
    return [assertion, assertion]


# Copyright (c) Meta Platforms, Inc. and affiliates. See LICENSE.

def make_direct_output_prompt(s):
    code, input = s
    return f"""You are given a Python function and an assertion containing an input to the function. Complete the assertion with a literal (no unsimplified expressions, no function calls) containing the output when executing the provided code on the given input, even if the function is incorrect or incomplete. Do NOT output any extra information. Provide the full assertion with the correct output in [ANSWER] and [/ANSWER] tags, following the examples.

[PYTHON]
def f(n):
    return n
assert f(17) == ??
[/PYTHON]
[ANSWER]
assert f(17) == 17
[/ANSWER]

[PYTHON]
def f(s):
    return s + "a"
assert f("x9j") == ??
[/PYTHON]
[ANSWER]
assert f("x9j") == "x9ja"
[/ANSWER]

[PYTHON]
{code}
assert f({input}) == ??
[/PYTHON]
[ANSWER]
"""


def make_direct_input_prompt(s):
    code, output = s
    return f"""You will be given a function f and an output in the form f(??) == output. Find any input such that executing f on the input leads to the given output. There may be multiple answers, but you should only output one. In [ANSWER] and [/ANSWER] tags, complete the assertion with one such input that will produce the output when executing the function.

[PYTHON]
def f(my_list):
    count = 0
    for i in my_list:
        if len(i) % 2 == 0:
            count += 1
    return count
assert f(??) == 3
[/PYTHON]
[ANSWER]
assert f(["mq", "px", "zy"]) == 3
[/ANSWER]

[PYTHON]
def f(s1, s2):
    return s1 + s2
assert f(??) == "banana"
[/PYTHON]
[ANSWER]
assert f("ba", "nana") == "banana"
[/ANSWER]

[PYTHON]
{code}
assert f(??) == {output}
[/PYTHON]
[ANSWER]
"""
