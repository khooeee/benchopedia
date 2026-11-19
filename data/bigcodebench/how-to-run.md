The authors' [bigcodebench](https://github.com/bigcode-project/bigcodebench/tree/09dd993f46c3fbf3a799465bb96d524edcb0b199) harness builds the prompts, extracts code from model output, runs each task's unit tests, and reports pass@k. It runs model-generated code, so run it in the authors' evaluation image, which also contains the many libraries the tasks import.

### 1. Start the evaluation environment

The image's v0.2.4 harness has the same scoring code as the pinned commit; later commits changed only generation backends. Save the Python steps below as `run_task.py` in the current directory and run them inside the image.

```sh
docker pull bigcodebench/bigcodebench-evaluate:v0.2.4
docker run -v "$(pwd)":/app --entrypoint python3 bigcodebench/bigcodebench-evaluate:v0.2.4 run_task.py
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream task number padded to four digits.

```python
from datasets import load_dataset

key = "{{key}}"
task_id = f"BigCodeBench/{int(key.removeprefix('bigcodebench-'))}"
dataset = load_dataset("bigcode/bigcodebench", split="v0.1.4", revision="b74c0d0bf70d2c0bc459be537895cca163007f1a")
problem = next(row for row in dataset if row["task_id"] == task_id)
```

### 3. Generate a solution

Choose the Instruct or Complete prompt. The harness sends a chat model that prompt after a fixed instruction, then `sanitize` keeps the target function and the code it depends on from the reply. A base model instead continues `complete_prompt` directly, and the harness sanitizes the prompt plus its continuation. The paper's main results use greedy decoding.

```python
from bigcodebench.provider.utility import make_raw_chat_prompt
from bigcodebench.sanitize import sanitize

split = "instruct"  # or "complete"
prompt = make_raw_chat_prompt(
    problem[f"{split}_prompt"], subset="full", split=split, tokenizer=None,
    instruction_prefix="Please provide a self-contained Python script that solves the following problem in a markdown code block:",
    response_prefix="Below is a Python script with a self-contained function that solves the problem and passes corresponding tests:",
)

def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return its reply.")

solution = sanitize(generate(prompt), entrypoint=problem["entry_point"])
```

### 4. Score it

Calibration, on by default, places the task's code prompt with a placeholder body before the solution, so imports the model left out are still defined. `check_correctness` then runs the task's unittest suite in a separate process with the command line's default memory limits and the harness's 240-second time limit.

```python
from bigcodebench.evaluate import check_correctness

calibrated = problem["code_prompt"] + "\n    pass\n" + solution
result = check_correctness(0, problem, calibrated, max_as_limit=30 * 1024, max_data_limit=30 * 1024,
                           max_stack_limit=10, min_time_limit=1, gt_time_limit=20)
print(result["base"][0])  # "pass", "fail", or "timeout"
```

### Score the full benchmark

Write one JSON line per sample, `{"task_id": ..., "solution": ...}`, with sanitized solutions for all 1,140 tasks, then run the image's default command. It first checks the reference solutions, then scores every sample and reports pass@1, pass@5 and pass@10, averaged over tasks, for each k no larger than the number of samples per task. The paper's headline figure is calibrated pass@1 with greedy decoding, reported separately for Instruct and Complete.

```sh
docker run -v "$(pwd)":/app bigcodebench/bigcodebench-evaluate:v0.2.4 --execution local --split instruct --subset full --samples samples.jsonl
```
