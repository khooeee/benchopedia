"""Grade original HumanEval completions against their pinned unit tests.

Use the prompt + completion + tests + check(entry_point) assembly and the
three-second deadline of the official evaluator. Run Python only inside the
network-isolated container.
https://github.com/openai/human-eval/blob/b9453e8f1865df0a0057a1383767caa400acfbcf/human_eval/execution.py
"""

import re
import subprocess
from uuid import uuid4


ATTEMPTS = 1
IMAGE = "python@sha256:a02e9c5406c416c504d6c9a1a306ff4080c3173f1008d192f953bd20382a2d5c"
TEST_START = re.compile(r"(?m)^(?:METADATA = |def check\(candidate\):)")
PROGRAM = """
import contextlib
import os
import signal
import sys

program = sys.stdin.read()
with open(os.devnull, "w") as silent:
    with contextlib.redirect_stdout(silent), contextlib.redirect_stderr(silent):
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, 3)
        exec(compile(program, "<humaneval>", "exec"), {})
        signal.setitimer(signal.ITIMER_REAL, 0)
print("humaneval-checks-passed")
"""


def split_task(task):
    _, _, fenced = task["prompt"].partition("\n\n")
    opening, _, code = fenced.partition("\n")
    fence = opening.removesuffix("python")
    prompt = code.removesuffix(fence)
    solution = task["solution"]
    if not fence or not code.endswith(fence) or not solution.startswith(prompt):
        raise ValueError(f"{task['key']}: missing original Python prompt")
    rest = solution[len(prompt):]
    start = TEST_START.search(rest)
    if start is None:
        raise ValueError(f"{task['key']}: missing original unit tests")
    return prompt, rest[:start.start()], rest[start.start():]


def check_setup():
    try:
        inspect = subprocess.run(
            ["docker", "image", "inspect", IMAGE], capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        inspect = None
    if inspect is None or inspect.returncode:
        return f"Start Docker and run docker pull {IMAGE}"
    return None


def messages(task):
    prompt, _, _ = split_task(task)
    return [
        {"role": "system", "content": "Return only the Python continuation of the provided prefix. "
         "Preserve indentation. Start where the prefix ends. Do not include Markdown fences."},
        {"role": "user", "content": prompt},
    ]


def reference_output(task):
    _, completion, _ = split_task(task)
    return completion


def grade(task, output):
    if not output.strip():
        return "unparseable", None
    prompt, _, tests = split_task(task)
    program = prompt + output + "\n" + tests
    name = f"benchopedia-humaneval-{uuid4().hex}"
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--name", name, "--pull=never", "--init",
             "--network", "none", "--read-only", "--cap-drop", "ALL",
             "--security-opt", "no-new-privileges", "--user", "65534:65534",
             "--memory", "128m", "--memory-swap", "128m", "--pids-limit", "16",
             "--cpus", "1", "--ulimit", "nofile=64:64", "-i", IMAGE,
             "python3", "-I", "-B", "-c", PROGRAM],
            input=program, capture_output=True, text=True, timeout=15,
        )
    except subprocess.TimeoutExpired:
        stopped = subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=10)
        if stopped.returncode and b"No such container" not in stopped.stderr:
            raise RuntimeError(f"Could not stop HumanEval container {name}")
        return "fail", "timed out"
    except FileNotFoundError:
        raise RuntimeError(check_setup()) from None
    if result.returncode in (125, 126, 127):
        raise RuntimeError(f"HumanEval sandbox could not start: {result.stderr.strip()}")
    if result.returncode == 142:
        return "fail", "timed out"
    if result.returncode == 0 and result.stdout.splitlines()[-1:] == ["humaneval-checks-passed"]:
        return "pass", "unit tests passed"
    return "fail", "unit tests failed"
