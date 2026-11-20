"""Run the official calibrated BigCodeBench Instruct grader in its evaluation image."""

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess
from uuid import uuid4


ATTEMPTS = 1
IMAGE = "bigcodebench/bigcodebench-evaluate@sha256:1327bddf60be9bc241648c59e6060cac4ca50248a0588ab735cd0200b17cc8c2"
INPUTS_SHA256 = "81c918f4462d251f23d4f90a76dc3386b7cf3254a11bf2c05b2b81ae00b772d0"
PREFIX = "Please provide a self-contained Python script that solves the following problem in a markdown code block:"
WORKER = """
import json
import sys
from bigcodebench.evaluate import check_correctness
from bigcodebench.sanitize import sanitize

request = json.load(sys.stdin)
record = request["problem"]
code = sanitize(request["output"], entrypoint=record["entry_point"])
if not code.strip():
    verdict = "unparseable"
else:
    calibrated = request["code_prompt"] + "\\n    pass\\n" + code
    result = check_correctness(0, record, calibrated, max_as_limit=30 * 1024,
                               max_data_limit=30 * 1024, max_stack_limit=10,
                               min_time_limit=1, gt_time_limit=20)
    verdict = result["base"][0]
print("benchopedia-verdict:" + verdict)
"""


def inputs_path():
    root = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
    return root / "build" / "bigcodebench-grading.json"


@lru_cache(maxsize=1)
def check_setup():
    path = inputs_path()
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != INPUTS_SHA256:
        return "Run python3 data/bigcodebench/setup_eval.py to install the pinned scoring inputs"
    try:
        state = subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True, timeout=10)
        if state.returncode == 0:
            return None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "Start Docker and run python3 data/bigcodebench/setup_eval.py to pull the evaluation image"


@lru_cache(maxsize=1)
def scoring_inputs():
    return json.loads(inputs_path().read_text(encoding="utf-8"))


def prompts(task):
    _, _, content = task["prompt"].partition("\n\n~~~python\n")
    complete, marker, instruct = content.partition("\n~~~\n\n## Instruct prompt\n\n~~~text\n")
    if not marker or not instruct.endswith("\n~~~"):
        raise ValueError(f"{task['key']}: missing a BigCodeBench prompt")
    return complete, instruct.removesuffix("\n~~~")


def messages(task):
    _, instruct = prompts(task)
    return [{"role": "user", "content": f"{PREFIX}\n{instruct.strip()}\n"}]


def reference_output(task):
    complete, _ = prompts(task)
    _, canonical_length = scoring_inputs()[task["key"]]
    return task["solution"][:len(complete) + 1 + canonical_length]


def grade(task, output):
    if not output.strip():
        return "unparseable", None
    code_prompt, _ = scoring_inputs()[task["key"]]
    ref = reference_output(task)
    problem = {
        "task_id": f"BigCodeBench/{int(task['key'].rsplit('-', 1)[1])}",
        "test": task["solution"][len(ref) + 1:],
        "entry_point": "task_func",
    }
    name = f"benchopedia-bigcode-{uuid4().hex}"
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--init", "--platform", "linux/amd64", "--name", name,
             "--pull=never", "--log-driver", "none", "--network", "none", "--read-only",
             "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--user", "65534:65534",
             "--memory", "4g", "--memory-swap", "4g", "--cpus", "2", "--pids-limit", "128",
             "--tmpfs", "/tmp:size=512m,mode=1777,nosuid", "--workdir", "/tmp",
             "-e", "MPLBACKEND=Agg", "-e", "MPLCONFIGDIR=/tmp/matplotlib",
             "-e", "OPENBLAS_NUM_THREADS=1", "--entrypoint", "python3",
             "-i", IMAGE, "-B", "-c", WORKER],
            input=json.dumps({"output": output, "problem": problem, "code_prompt": code_prompt}),
            capture_output=True, text=True, timeout=255,
        )
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=10)
        return "fail", "timed out"
    status = next((line.partition(":")[2] for line in reversed(result.stdout.splitlines())
                   if line.startswith("benchopedia-verdict:")), None)
    if result.returncode or status not in ("pass", "fail", "timeout", "unparseable"):
        raise RuntimeError(f"{task['key']}: BigCodeBench evaluator failed to report a verdict")
    if status == "unparseable":
        return "unparseable", None
    return ("pass" if status == "pass" else "fail"), status
