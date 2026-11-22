"""Execute one Python test program in a fresh pinned Docker sandbox."""

import subprocess
from uuid import uuid4


IMAGE = "python@sha256:a02e9c5406c416c504d6c9a1a306ff4080c3173f1008d192f953bd20382a2d5c"
PROGRAM = """
import contextlib
import os
import signal
import sys

program = sys.stdin.read()
with open(os.devnull, "w") as silent:
    with contextlib.redirect_stdout(silent), contextlib.redirect_stderr(silent):
        signal.signal(signal.SIGALRM, signal.SIG_DFL)
        signal.setitimer(signal.ITIMER_REAL, float(sys.argv[1]))
        exec(compile(program, "<humaneval>", "exec"), {})
        signal.setitimer(signal.ITIMER_REAL, 0)
print("benchopedia-checks-passed")
"""


def check_setup():
    try:
        inspect = subprocess.run(
            ["docker", "image", "inspect", IMAGE], capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        inspect = None
    if inspect is None or inspect.returncode:
        return "Start Docker and run python3 runner/python_sandbox.py"
    return None


def execute(program, timeout):
    name = f"benchopedia-python-{uuid4().hex}"
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--name", name, "--pull=never", "--init", "--log-driver", "none",
             "--network", "none", "--read-only", "--cap-drop", "ALL",
             "--security-opt", "no-new-privileges", "--user", "65534:65534",
             "--memory", "128m", "--memory-swap", "128m", "--pids-limit", "16",
             "--cpus", "1", "--ulimit", "nofile=64:64", "-i", IMAGE,
             "python3", "-I", "-B", "-c", PROGRAM, str(timeout)],
            input=program, capture_output=True, text=True, timeout=timeout + 12,
        )
    except subprocess.TimeoutExpired:
        stopped = subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=10)
        if stopped.returncode and b"No such container" not in stopped.stderr:
            raise RuntimeError(f"Could not stop Python container {name}")
        return "timed out"
    except FileNotFoundError:
        raise RuntimeError(check_setup()) from None
    if result.returncode in (125, 126, 127):
        raise RuntimeError(f"Python sandbox could not start: {result.stderr.strip()}")
    if result.returncode == 142:
        return "timed out"
    if result.returncode == 0 and result.stdout.splitlines()[-1:] == ["benchopedia-checks-passed"]:
        return "passed"
    return "failed"


if __name__ == "__main__" and check_setup() is not None:
    subprocess.run(["docker", "pull", IMAGE], check=True)
