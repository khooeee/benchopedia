MBPP's authors publish the [problems and their prompt format](https://github.com/google-research/google-research/blob/bb18d9b0cb460fee1a080fa2eeb4109fe3805275/mbpp/README.md) but no grader, so the scoring below implements the rule from the [paper](https://arxiv.org/abs/2108.07732): a program solves a problem when it passes the problem's three test assertions. Scoring runs model-generated code, so run it inside a sandbox such as a container or disposable virtual machine.

### 1. Fetch the data

The scoring below needs only Python's standard library.

```sh
curl -LO https://raw.githubusercontent.com/google-research/google-research/bb18d9b0cb460fee1a080fa2eeb4109fe3805275/mbpp/mbpp.jsonl
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream task ID padded to four digits.

```python
import json

key = "{{key}}"
task_id = int(key.removeprefix("mbpp-"))
with open("mbpp.jsonl", encoding="utf-8") as f:
    problems = {row["task_id"]: row for row in map(json.loads, f)}
problem = problems[task_id]
```

### 3. Generate a program

The authors' prompts showed three solved examples, task IDs 2, 3 and 4, then the task and its three tests in the README's template. The model writes code after `[BEGIN]`, and `[DONE]` marks its end. The README does not say what separates the examples; this uses a newline.

```python
def task_prompt(row):
    tests = "\n".join(row["test_list"])
    return (f"You are an expert Python programmer, and here is your task: {row['text']} "
            f"Your code should pass these tests:\n\n{tests}\n[BEGIN]\n")

few_shot = "".join(f"{task_prompt(problems[i])}{problems[i]['code']}\n[DONE]\n" for i in (2, 3, 4))

def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return the text it writes after [BEGIN].")

code = generate(few_shot + task_prompt(problem)).split("[DONE]")[0]
```

### 4. Score it

The program runs in a fresh Python process with the task's setup code before it and its three tests after it. It passes when every assertion holds. The paper sets no time limit, so ten seconds here is a choice. The additional tests some problems carry are not part of the score.

```python
import subprocess
import sys
import tempfile

def passes(row, code: str, timeout: float = 10.0) -> bool:
    program = "\n".join([row["test_setup_code"], code, *row["test_list"]])
    with tempfile.TemporaryDirectory() as workdir:
        try:
            run = subprocess.run([sys.executable, "-c", program], cwd=workdir, capture_output=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return False
    return run.returncode == 0

print("passed" if passes(problem, code) else "failed")
```

### Score the full benchmark

The test split is task IDs 11 through 510. The paper drew 80 samples per problem at temperature 0.5 and reported two numbers: the fraction of problems solved by any sample and the fraction of all samples that pass.

```python
results = {i: [passes(problems[i], generate(few_shot + task_prompt(problems[i])).split("[DONE]")[0])
               for _ in range(80)] for i in range(11, 511)}
print("problems solved:", sum(any(r) for r in results.values()) / len(results))
print("samples passing:", sum(map(sum, results.values())) / (80 * len(results)))
```
