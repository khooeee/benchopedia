The authors' [human-eval](https://github.com/openai/human-eval/tree/b9453e8f1865df0a0057a1383767caa400acfbcf) package loads this task, executes a completion against its unit tests, and reports pass@k. It runs model-generated code, so run it inside a sandbox such as a container or disposable virtual machine.

### 1. Install the harness

```sh
git clone https://github.com/openai/human-eval
git -C human-eval checkout b9453e8f1865df0a0057a1383767caa400acfbcf
pip install "setuptools<82"  # its setup.py imports pkg_resources
pip install --no-build-isolation -e human-eval
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream task ID's number padded to three digits.

```python
from human_eval.data import read_problems

key = "{{key}}"
task_id = f"HumanEval/{int(key.removeprefix('humaneval-'))}"
problem = read_problems()[task_id]
```

### 3. Generate a completion

The model receives the prompt exactly as published and returns only the code that continues it, normally the function body.

```python
def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return its continuation of the prompt.")

completion = generate(problem["prompt"])
```

### 4. Score it

`check_correctness` appends the completion to the prompt, runs the task's tests with the harness's default three-second timeout, and reports whether they pass.

```python
from human_eval.execution import check_correctness

result = check_correctness(problem, completion, timeout=3.0)
print(result["result"])  # "passed", "failed: ...", or "timed out"
```

### Score the full benchmark

Write one JSON line per sample, `{"task_id": ..., "completion": ...}`, covering all 164 tasks, then run the authors' scorer. It reports pass@k, averaged over tasks, for each k no larger than the number of samples per task.

```sh
evaluate_functional_correctness samples.jsonl
```
