The authors' [evaluation script](https://github.com/zai-org/CodeGeeX/blob/2838420b7b4492cf3d16bce5320e26e65960c9e2/codegeex/benchmark/humaneval-x/evaluate_humaneval_x.py) in the CodeGeeX repository joins the prompt, a completion and the task's tests, compiles and runs the program, and reports pass@k. It runs model-generated code, so run it inside the authors' Docker image, which also provides the compilers and runtimes for all five languages.

### 1. Start the evaluation environment

The image contains a September 2022 CodeGeeX checkout, before the JavaScript fixes, so move it to the pinned commit. That commit ships with the Java test run commented out, as the README warns; uncomment it to score Java.

```sh
docker run -it rishubi/codegeex:latest bash
# inside the container:
cd /workspace/CodeGeeX
git fetch origin
git checkout 2838420b7b4492cf3d16bce5320e26e65960c9e2
sed -i "s/# exec_result = subprocess.run(\[f'java'/exec_result = subprocess.run([f'java'/" codegeex/benchmark/execution.py
```

### 2. Load this task

Benchopedia's key `{{key}}` is the language and the upstream problem number padded to three digits. Run the Python below from `/workspace/CodeGeeX`.

```python
import os

from codegeex.benchmark.evaluate_humaneval_x import LANGUAGE_NAME, process_humaneval_test
from codegeex.benchmark.utils import read_dataset

key = "{{key}}"
language, number = key.rsplit("-", 1)
lang = "js" if language == "javascript" else language  # the data folder name
task_id = f"{LANGUAGE_NAME[lang]}/{int(number)}"
data_dir = os.path.abspath("codegeex/benchmark/humaneval-x")
problems = read_dataset(f"{data_dir}/{lang}/data/humaneval_{lang}.jsonl.gz", dataset_type="humaneval")
problem = problems[task_id]
```

### 3. Generate a completion

The model receives the prompt, a declaration and docstring, and continues it with the function body. The authors' generation code trims each completion with `cleanup_code`, for example cutting C++, Java, JavaScript and Go output after its last closing brace.

```python
from codegeex.benchmark.utils import cleanup_code

def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return its continuation of the prompt.")

generation = cleanup_code(generate(problem["prompt"]), language_type=lang, dataset="humaneval")
```

### 4. Score it

`process_humaneval_test` assembles the program as the evaluation script does, adding standard imports and the test program. `check_correctness` then compiles and runs it with the shell script's default five-second timeout.

```python
from codegeex.benchmark.execution import check_correctness

sample = {"task_id": task_id, "prompt": problem["prompt"], "generation": generation}
sample["test_code"] = process_humaneval_test(sample, problems)
result = check_correctness(task_id, sample, lang, timeout=5.0, tmp_dir=f"{data_dir}/{lang}/evaluation")
print(result["result"])  # "passed", "failed: ...", or "timed out"
```

### Score the full benchmark

For each language, write one JSON line per sample, `{"task_id": "CPP/0", "generation": ...}`, covering all 164 problems, then pass the file, the language's folder name, the worker count and the timeout to the authors' script. Keep the file outside `codegeex/benchmark/humaneval-x` and leave `-to-` out of its name, because the script treats those as ground-truth and translation runs. It writes per-sample results beside the input and prints pass@1, pass@10 and pass@100, averaged over the problems, for each k no larger than the number of samples per problem.

```sh
bash scripts/evaluate_humaneval_x.sh samples_cpp.jsonl cpp 64 5
```

### Verify with the Benchopedia sweep

With Docker running, run `python3 data/humaneval-x/setup_eval.py` and
`python3 runner/sweep.py humaneval-x --verify-grader`. Each completion runs in
the pinned CodeGeeX image without network access or host mounts, with the
published compilation and execution limits. The build preloads the pinned Go modules. Java assertions are enabled.
The sweep records pass or fail for individual samples.
