"""Score IFEval with the pinned official strict prompt-level evaluator."""

import json
import os
from pathlib import Path
import subprocess

ATTEMPTS = 2
REVISION = "e6890f85757dd84e27ca6df2dd30651dafad28e0"
ROOT = next(parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists())
RUNTIME = ROOT / "build" / "ifeval"
UPSTREAM = RUNTIME / "upstream"
INPUTS = UPSTREAM / "instruction_following_eval" / "data" / "input_data.jsonl"
PYTHON = RUNTIME / "venv" / "bin" / "python"
READY = RUNTIME / "ready"

WORKER = """
import json
import sys

import langdetect
from instruction_following_eval import evaluation_lib

langdetect.DetectorFactory.seed = 0
key, prompt, response = json.load(sys.stdin)
example = next(row for row in evaluation_lib.read_prompt_list(sys.argv[1]) if row.key == int(key))
if prompt != example.prompt:
    raise ValueError(f"{key}: the installed IFEval record differs from the imported task")
result = evaluation_lib.test_instruction_following_strict(example, {example.prompt: response})
print(json.dumps(result.follow_all_instructions))
"""


def setup_error():
    if not (READY.is_file() and PYTHON.is_file() and INPUTS.is_file()):
        return "run python3.11 data/ifeval/setup_eval.py to install the pinned IFEval evaluator"
    if READY.read_text(encoding="utf-8").strip() != REVISION:
        return "rerun python3.11 data/ifeval/setup_eval.py to update the pinned IFEval evaluator"
    return None


def messages(task):
    return [{"role": "user", "content": task["prompt"]}]


def grade(task, output):
    error = setup_error()
    if error is not None:
        raise RuntimeError(error)
    environment = os.environ | {"PYTHONPATH": str(UPSTREAM), "NLTK_DATA": str(RUNTIME / "nltk_data")}
    result = subprocess.run(
        [str(PYTHON), "-c", WORKER, str(INPUTS)],
        input=json.dumps([task["key"], task["prompt"], output]),
        env=environment, check=True, capture_output=True, text=True, timeout=30,
    )
    return ("pass" if json.loads(result.stdout) else "fail"), output
