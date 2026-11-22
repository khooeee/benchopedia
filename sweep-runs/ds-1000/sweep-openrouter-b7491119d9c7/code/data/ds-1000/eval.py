"""Evaluate DS-1000 code with its pinned execution and string checks.

The test assembly and timeout follow the authors' test_ds1000.py.
https://github.com/xlang-ai/DS-1000/blob/b39aab71da6d23ef8d3cac59a7c5f834516ab334/test_ds1000.py
"""

from functools import lru_cache
import gzip
import hashlib
import json
from pathlib import Path
import subprocess
from uuid import uuid4


ATTEMPTS = 1
REVISION = "b39aab71da6d23ef8d3cac59a7c5f834516ab334"
ARCHIVE_SHA256 = "e8c6daa9d7223976bce0296644f3933f78d7f47830669ff05cd61da62c6ba9b3"
IMAGE = "benchopedia-ds1000:b39aab7"
TIMEOUT = 120
WORKER = """
import contextlib
import os
import signal
import sys

program = sys.stdin.read()
signal.alarm(120)
with open(os.devnull, "w") as silent:
    with contextlib.redirect_stdout(silent), contextlib.redirect_stderr(silent):
        exec(compile(program, "<ds1000>", "exec"), {})
signal.alarm(0)
print("benchopedia-ds1000-passed")
"""


def archive_path():
    root = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
    return root / "build" / "ds1000.jsonl.gz"


@lru_cache(maxsize=1)
def check_setup():
    archive = archive_path()
    if not archive.is_file() or hashlib.sha256(archive.read_bytes()).hexdigest() != ARCHIVE_SHA256:
        return "Run python3 data/ds-1000/setup_eval.py to install the pinned test data"
    try:
        result = subprocess.run(
            ["docker", "image", "inspect", "--format", '{{index .Config.Labels "org.benchopedia.ds1000"}}', IMAGE],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip() == REVISION:
            return None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "Start Docker and run python3 data/ds-1000/setup_eval.py to build the evaluation image"


@lru_cache(maxsize=1)
def contexts():
    with gzip.open(archive_path(), "rt", encoding="utf-8") as source:
        return {int(row["metadata"]["problem_id"]): row["code_context"] for row in map(json.loads, source)}


def messages(task):
    _, _, prompt = task["prompt"].partition("\n\n~~~text\n")
    if not prompt.endswith("\n~~~"):
        raise ValueError(f"{task['key']}: missing DS-1000 prompt")
    return [
        {"role": "system", "content": "Return the requested Python completion between <code> and </code> tags."},
        {"role": "user", "content": prompt.removesuffix("\n~~~")},
    ]


def postprocess(output):
    code = output.split("</code>", 1)[0].replace("```python", "")
    code = code.split("```", 1)[0].split("\nEND SOLUTION", 1)[0]
    return code.replace("<code>", "")


def grade(task, output):
    answer = postprocess(output)
    if not answer.strip():
        return "unparseable", None
    number = int(task["key"].removeprefix("problem-"))
    context = contexts()[number]
    program = f"{context}\ncode = {answer!r}\ntest_execution(code)\n"
    if "test_string(" in context:
        program += "test_string(code)\n"

    name = f"benchopedia-ds1000-{uuid4().hex}"
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--init", "--platform", "linux/amd64", "--pull=never",
             "--name", name, "--log-driver", "none", "--network", "none", "--read-only",
             "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--user", "65534:65534",
             "--cpus", "2", "--memory", "3g", "--memory-swap", "3g", "--pids-limit", "128",
             "--tmpfs", "/tmp:size=512m,mode=1777,nosuid", "--workdir", "/tmp", "-i",
             IMAGE, "-c", WORKER],
            input=program, capture_output=True, text=True, timeout=TIMEOUT + 15,
        )
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=10)
        return "fail", "timed out"
    if result.returncode in (125, 126, 127):
        raise RuntimeError(f"DS-1000 sandbox could not start: {result.stderr.strip()}")
    if result.returncode == 142:
        return "fail", "timed out"
    if result.returncode == 0 and result.stdout.splitlines()[-1:] == ["benchopedia-ds1000-passed"]:
        return "pass", "test checks passed"
    return "fail", "test checks failed"
