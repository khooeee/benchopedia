The authors' [test script](https://github.com/xlang-ai/DS-1000/blob/b39aab71da6d23ef8d3cac59a7c5f834516ab334/test_ds1000.py) runs each problem's tests on a generated answer and reports the share of problems solved. It runs model-generated code without restrictions, since plotting and machine-learning libraries need file and system access, so run it inside a sandbox such as a Linux container or disposable virtual machine. Its execution helper relies on Linux process forking.

### 1. Install the environment

The authors pin Python 3.10 and the library versions in a conda environment.

```sh
git clone https://github.com/xlang-ai/DS-1000
git -C DS-1000 checkout b39aab71da6d23ef8d3cac59a7c5f834516ab334
conda env create -f DS-1000/environment.yml
conda activate ds1000-3.10
pip install datasets tqdm  # the README notes the test code also needs these
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream `problem_id` padded to three digits. The test script's `data/ds1000.jsonl.gz` is identical to the snapshot's Hugging Face revision. Save the Python steps as a script inside `DS-1000` and run it from there.

```python
from test_ds1000 import ds1000, postprocess

key = "{{key}}"
problem_id = int(key.removeprefix("problem-"))
problem = ds1000[problem_id]
assert problem["metadata"]["problem_id"] == problem_id
```

### 3. Generate an answer

The model receives the prompt as published and writes the code that replaces the gap the prompt ends on. The authors' generation scripts stop at `</code>` or `# SOLUTION END`, and their API runner adds a system prompt asking for code between `<code>` and `</code>` tags. `postprocess` strips such tags and Markdown fences, as the test script does.

```python
def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model, stopping at </code> or # SOLUTION END, and return its code.")

answer = postprocess(generate(problem["prompt"]))
```

### 4. Score it

The test script appends the answer to the problem's `code_context`, calls `test_execution` and, where the context defines it, `test_string`, and runs the program in its own process with a 120-second limit.

```python
import execution

test_program = (
    problem["code_context"] + "\n"
    + f"code = {repr(answer)}\n"
    + "test_execution(code)\n"
    + ("test_string(code)\n" if "test_string(" in problem["code_context"] else "\n")
)
result = execution.check_correctness(test_program, timeout=120, completion_id=problem_id)
print(result["result"])  # "passed", "failed: ...", or "timed out"
```

### Score the full benchmark

Write `data/<model>-answers.jsonl` with one line, `{"code": ...}`, per problem in `problem_id` order, then run the script from the `DS-1000` directory. It scores each problem 1 or 0 and writes the mean overall, by library and by perturbation type to `results/<model>-result.txt`. The paper's pass@1 averages this score over 40 samples per problem drawn at temperature 0.2.

```sh
python test_ds1000.py --model <model>
```

### Verify with the Benchopedia sweep

Run `python3 data/ds-1000/setup_eval.py` with Docker running, then run
`python3 runner/sweep.py ds-1000 --verify-grader`. The evaluator uses the pinned
test contexts and the published dependency versions. It runs each answer in a
fresh, network-isolated CPU container and records whether the execution and
any string checks pass. Test data remain under the ignored build directory.
