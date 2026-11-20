"""Grade HumanEval-X continuations with the original resources and test assembly.

The pinned CodeGeeX functions and import lists at the bottom retain the
upstream implementation under Apache 2.0. See LICENSE.
https://github.com/zai-org/CodeGeeX/tree/2838420b7b4492cf3d16bce5320e26e65960c9e2/codegeex/benchmark
"""

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess
from uuid import uuid4


ATTEMPTS = 1
IMAGE = "rishubi/codegeex@sha256:dae21e19f49f46144c45f0f5566a02b05f2735ca1db49b1ac5f1b8cd455825e0"
GO_FILES = {
    "go.mod": "cea5dade02a8e4daa766c97f84b5c51f2ab921681908f03b1a833b2035b9347b",
    "go.sum": "40565af0c7bc9299286ac5e13c801b6b984d21c7401f09a09fff8ce1849e4dc7",
}
INPUTS_SHA256 = "e8d9e79d695b4dcec8b8af83fecc467bf67a62d3f3a4f1530f3ee15be990bc3d"
WORKER = """
import json
import os
import shutil
import tempfile
import subprocess
import sys
from pathlib import Path

task = json.load(sys.stdin)
language = task["language"]
os.chdir(tempfile.mkdtemp(dir="/tmp"))
if language == "go":
    for name in ("go.mod", "go.sum"):
        shutil.copyfile("/opt/benchopedia-go/" + name, name)
    shutil.copytree("/opt/benchopedia-go/cache", "/tmp/gocache")
file, commands = {
    "python": ("test.py", [["python3", "-I", "-B", "test.py"]]),
    "cpp": ("test.cpp", [["/usr/bin/g++", "-std=c++11", "test.cpp"] +
                        (["-lcrypto", "-lssl"] if task["number"] == 162 else []), ["./a.out"]]),
    "java": ("Main.java", [["javac", "Main.java"], ["java", "-ea", "-cp", ".", "Main"]]),
    "javascript": ("test.js", [["node", "test.js"]]),
    "go": ("main_test.go", [["go", "test", "-timeout=5s", "main_test.go"]]),
}[language]
Path(file).write_text(task["program"], encoding="utf-8")
status = "passed"
for command in commands:
    try:
        result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
    except subprocess.TimeoutExpired:
        status = "timed out"
        break
    if result.returncode != 0:
        status = "failed"
        break
print("benchopedia-verdict:" + status)
"""


def inputs_path():
    root = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
    return root / "build" / "humaneval-x-boundaries.json"


def go_dir():
    return inputs_path().parent / "humaneval-x-go"


def go_ready():
    root = go_dir()
    return ((root / "cache").is_dir() and (root / "modules").is_dir()
            and all((root / name).is_file() and hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
                    for name, digest in GO_FILES.items()))


@lru_cache(maxsize=1)
def check_setup():
    path = inputs_path()
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != INPUTS_SHA256:
        return "Run python3 data/humaneval-x/setup_eval.py to install the pinned test metadata"
    if not go_ready():
        return "Run python3 data/humaneval-x/setup_eval.py to download the pinned Go modules and prepare the cache"
    try:
        result = subprocess.run(["docker", "image", "inspect", IMAGE], capture_output=True, timeout=10)
        if result.returncode == 0:
            return None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "Start Docker and run python3 data/humaneval-x/setup_eval.py to prepare the pinned CodeGeeX runtime"


@lru_cache(maxsize=1)
def boundaries():
    return json.loads(inputs_path().read_text(encoding="utf-8"))


def split_prompt(task):
    title, _, fenced = task["prompt"].partition("\n\n~~~")
    _, _, code = fenced.partition("\n")
    if not code.endswith("~~~"):
        raise ValueError(f"{task['key']}: missing HumanEval-X prompt")
    return title.split(": ", 1)[0], code.removesuffix("~~~")


def messages(task):
    _, prompt = split_prompt(task)
    instruction = ("Return only the code that continues the provided prefix. Preserve indentation. "
                   "Do not include Markdown fences.")
    return [{"role": "system", "content": instruction}, {"role": "user", "content": prompt}]


def reference_output(task):
    _, prompt = split_prompt(task)
    length, *_ = boundaries()[task["key"]]
    return task["solution"][len(prompt):len(prompt) + length]


def grade(task, output):
    task_id, prompt = split_prompt(task)
    language, number = task["key"].rsplit("-", 1)
    length, *go_setup = boundaries()[task["key"]]
    language_type = "js" if language == "javascript" else language
    generation = cleanup_code(output, language_type, "humaneval")
    if not generation.strip():
        return "unparseable", None
    sample = {"task_id": task_id, "prompt": prompt, "generation": generation}
    record = {"test": task["solution"][len(prompt) + length + 1:]}
    if go_setup:
        record["import"], record["test_setup"] = go_setup
    program = process_humaneval_test(sample, {task_id: record})

    container = f"benchopedia-humanevalx-{uuid4().hex}"
    go_mount = []
    if language == "go":
        go_mount = ["--mount", f"type=bind,src={go_dir()},dst=/opt/benchopedia-go,readonly",
                    "-e", "GOMODCACHE=/opt/benchopedia-go/modules", "-e", "GOPROXY=off"]
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--init", "--platform", "linux/amd64", "--name", container,
             "--pull=never", "--log-driver", "none", "--network", "none", "--read-only",
             "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--user", "65534:65534",
             "--memory", "1g", "--memory-swap", "1g", "--cpus", "2", "--pids-limit", "96",
             "--tmpfs", "/tmp:size=512m,mode=1777,exec,nosuid", "--workdir", "/tmp", *go_mount,
             "-e", "GOCACHE=/tmp/gocache", "-e", "GOPATH=/tmp/go", "-e", "GOMAXPROCS=2",
             "-e", "JAVA_TOOL_OPTIONS=-Xmx256m", "--entrypoint", "python3", "-i", IMAGE, "-I", "-B", "-c", WORKER],
            input=json.dumps({"language": language, "number": int(number), "program": program}),
            capture_output=True, text=True, timeout=30,
        )
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True, timeout=10)
        return "fail", "timed out"
    status = next((line.partition(":")[2] for line in reversed(result.stdout.splitlines())
                   if line.startswith("benchopedia-verdict:")), None)
    if result.returncode or status not in ("passed", "failed", "timed out"):
        raise RuntimeError(f"{task['key']}: CodeGeeX sandbox failed to report a verdict")
    return ("pass" if status == "passed" else "fail"), status


# Pinned CodeGeeX helpers retained under the accompanying Apache 2.0 license.

IMPORT_HELPER = {
    "python": [
        "import math",
        "import re",
        "import sys",
        "import copy",
        "import datetime",
        "import itertools",
        "import collections",
        "import heapq",
        "import statistics",
        "import functools",
        "import hashlib",
        "import numpy",
        "import numpy as np",
        "import string",
        "from typing import *",
        "from collections import *",
    ],
    "go"    : [
        "math",
        "strings",
        "fmt",
        "strconv",
        "time",
        "bytes",
        "regexp",
        "sort",
        "math/rand",
        "crypto/md5",
    ],
    "cpp"   : [
        "#include<stdlib.h>",
        "#include<algorithm>",
        "#include<math.h>",
        "#include<stdio.h>",
        "#include<vector>",
        "#include<string>",
        "#include<climits>",
        "#include<cstring>",
        "#include<iostream>",
    ],
}


def cleanup_code(
    code: str,
    language_type: str = None,
    dataset: str = None,
):
    """
    Cleans up the generated code.
    """
    if language_type is None or dataset is None:
        return code

    if "humaneval" in dataset.lower():
        if language_type.lower() == "python":
            end_words = ["\ndef", "\nclass", "\nif", "\n#", "\nprint", "\nassert"]
            for w in end_words:
                if w in code:
                    code = code[:code.rfind(w)]
        elif language_type.lower() == "java":
            main_pos = code.find("public static void main")
            if main_pos != -1:
                code = code[:main_pos] + '}'
            if '}' in code:
                code = code[:code.rfind('}')] + '}'
            if code.count('{') + 1 == code.count('}'):
                code += "\n}"
        elif language_type.lower() == "go":
            end_words = ["\n//", "\nfunc main("]
            for w in end_words:
                if w in code:
                    code = code[:code.rfind(w)]
            if '}' in code:
                code = code[:code.rfind('}')] + '}'
        elif language_type.lower() == "cpp":
            if '}' in code:
                code = code[:code.rfind('}')] + '}'
        elif language_type.lower() == "js":
            if '}' in code:
                code = code[:code.rfind('}')] + '}'

    return code


def process_humaneval_test(sample, problems, example_test=False):
    task_id = sample["task_id"]
    language = task_id.split("/")[0].lower()

    prompt = sample["prompt"]
    if example_test and "example_test" in problems[task_id] and problems[task_id]["example_test"] != "":
        test = problems[task_id]["example_test"]
    else:
        test = problems[task_id]["test"]
    code = sample["generation"]

    # Pre-process for different languages
    if language == "python":
        code_ = []
        for line in code.split("\n"):
            if (len(line.strip()) > 0 and line[0] != ' ' and line[0] != '\t'):
                break
            code_.append(line)
        code = "\n".join(code_)
        test_setup = "\n".join(IMPORT_HELPER["python"]) + "\n"
        test_string = test_setup + prompt + code + "\n" + test + "\n"
    elif language == "cpp":
        test_set_up = ""
        for s in IMPORT_HELPER["cpp"]:
            if s not in prompt:
                test_set_up += s + "\n"
        test_string = test_set_up + "\n" + prompt + code + "\n" + test
    elif language == "java":
        test_string = prompt + code + "\n" + test
    elif language == "js" or language == "javascript":
        test_string = prompt + code + "\n" + test
    elif language == "go":
        import_string = problems[task_id]["import"]
        prompt = prompt.replace(import_string, "")
        if example_test and "example_test" in problems[task_id]:
            test = problems[task_id]["example_test"]
        else:
            test = problems[task_id]["test"]
        test_setup = problems[task_id]["test_setup"]
        other_pkgs = []
        for pkg in IMPORT_HELPER["go"]:
            if pkg not in test_setup:
                p = pkg.split("/")[-1]
                if p + "." in code:
                    other_pkgs.append(f"\"{pkg}\"")
        if other_pkgs:
            import_other_pkgs = "import (\n" + "    ".join([p + "\n" for p in other_pkgs]) + ")"
            test_string = test_setup + "\n" + import_other_pkgs + "\n" + prompt + code + "\n" + test
        else:
            test_string = test_setup + "\n" + prompt + code + "\n" + test
    elif language == "rust":
        main = "\nfn main(){ \n } \n"
        declaration = problems[task_id]["declaration"]
        test_string = main + declaration + prompt + code + test

    return test_string
