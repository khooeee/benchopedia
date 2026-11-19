The authors' [evaluate.py](https://github.com/google-deepmind/bbeh/blob/80d12ca916b7158f22293fcf3144f4d3d854d4be/bbeh/evaluate.py) extracts the final answer after "The answer is:" and compares it with the target using a few normalization rules. The prompt adds the answer-format suffix given in the paper's [reproducibility appendix](https://arxiv.org/html/2502.19187v2#A3).

### 1. Fetch the data and grader

```sh
git clone https://github.com/google-deepmind/bbeh
git -C bbeh checkout 80d12ca916b7158f22293fcf3144f4d3d854d4be
```

### 2. Load this task

Benchopedia's key `{{key}}` is the task directory name without its `bbeh_` prefix, with hyphens for underscores, followed by the example's one-based position in that directory's `task.json`.

```python
import json
import sys
from pathlib import Path

key = "{{key}}"
group, number = key.rsplit("-", 1)
task_file = Path(f"bbeh/bbeh/benchmark_tasks/bbeh_{group.replace('-', '_')}/task.json")
example = json.loads(task_file.read_text(encoding="utf-8"))["examples"][int(number) - 1]
```

### 3. Generate an answer

The paper appends this suffix to every question. It does not say how the two are joined; a blank line is used here.

```python
SUFFIX = (
    'Think step by step, and when you provide the final answer, please use the prefix "The answer is:" '
    "without any modification, and provide the answer directly, with no formatting, no bolding, and no "
    'markup. For instance: "The answer is: 42" or "The answer is: yes". If the question is multiple '
    "choice with a single correct answer, the final answer must only be the letter corresponding to the "
    'correct answer. For example, "The answer is: (a)".'
)

def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return its full response.")

response = generate(example["input"] + "\n\n" + SUFFIX)
```

### 4. Score it

`evaluate_correctness` lowercases both sides and accepts simple variants such as a bare choice letter, equal numbers, or removed quotes and brackets. Importing the file also prints its eight built-in examples. It drops a trailing period from the response but not from the target, so 11 Linguini targets that end in a period can never match.

```python
sys.path.insert(0, "bbeh/bbeh")
from evaluate import evaluate_correctness

print(evaluate_correctness(response, example["target"]))
```

### Score the full benchmark

The repository has no batch runner. Score every example in the 23 `task.json` files and compute accuracy in percent for each task. The paper's headline BBEH score is the harmonic mean of the 23 accuracies after adding 1 to each to handle zero accuracies, with nothing subtracted afterwards; BBEH Mini instead uses plain accuracy over its 460 examples.

```python
from statistics import harmonic_mean

accuracy = {}  # task directory -> percent correct
print(harmonic_mean([percent + 1 for percent in accuracy.values()]))
```
