The authors' [evaluation script](https://github.com/hendrycks/math/blob/985bdc1696e88e8643f081a0ff4719da39f2ae2a/modeling/evaluate_gpt3.py) prompts with eight solved examples, takes the model's short answer, and compares it with the reference's last boxed answer using `is_equiv` from [math_equivalence.py](https://github.com/hendrycks/math/blob/985bdc1696e88e8643f081a0ff4719da39f2ae2a/modeling/math_equivalence.py). The problems come from the EleutherAI/hendrycks_math mirror at the pinned revision.

### 1. Fetch the scorer and install the data loader

```sh
git clone https://github.com/hendrycks/math hendrycks-math
git -C hendrycks-math checkout 985bdc1696e88e8643f081a0ff4719da39f2ae2a
pip install datasets
```

### 2. Load this task

Benchopedia's key `{{key}}` is the subject's configuration name, `-test-`, and the problem's one-based row in that subject's test split.

```python
import re
import sys
from pathlib import Path

from datasets import load_dataset

sys.path.insert(0, "hendrycks-math/modeling")
from dataset.util import last_boxed_only_string
from math_equivalence import is_equiv

REVISION = "21a5633873b6a120296cce3e2df9d5550074f4a3"
key = "{{key}}"
subject, number = key.rsplit("-test-", 1)
row = load_dataset("EleutherAI/hendrycks_math", subject, split="test", revision=REVISION)[int(number) - 1]
```

### 3. Generate an answer

The script appends the problem and `Answer: $` to its eight examples, decodes greedily for up to 20 tokens, and keeps the text before the next `$`, `###` or newline. It cannot be imported, because it expects an API key pasted into the file, so this reads its `train_prompt` lines. Python may warn about their backslash escapes; the strings are the same as when the script runs.

```python
script = Path("hendrycks-math/modeling/evaluate_gpt3.py").read_text(encoding="utf-8")
namespace = {}
exec("\n".join(line for line in script.splitlines() if line.startswith("train_prompt")), namespace)
train_prompt = namespace["train_prompt"]

def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model greedily for up to 20 tokens and return its continuation.")

model_output = re.split(r"\$|###|\n", generate(train_prompt + "\n" + row["problem"] + "\nAnswer: $"))[0]
```

### 4. Score it

The reference answer is the last `\boxed{...}` in the worked solution with the box removed by the script's `remove_boxed`, repeated here. `is_equiv` normalizes fractions, square roots, units and spacing, then compares the strings exactly. If your model writes a full solution instead, extract its answer the same way, as the authors' `eval_math_gpt.py` does.

```python
def remove_boxed(s):  # as defined in evaluate_gpt3.py
    left = "\\boxed{"
    return s[len(left):-1] if s and s.startswith(left) and s.endswith("}") else None

answer = remove_boxed(last_boxed_only_string(row["solution"]))
print(model_output, answer, is_equiv(model_output, answer))
```

### Score the full benchmark

The script's `run` function cannot be used as is: it calls GPT-3 engines through the pre-1.0 `openai` package and walks the original archive's per-problem JSON files. Score every test problem in the seven subject configurations as above. The script reports accuracy for each subject and difficulty level, and overall accuracy, the fraction of all 5,000 problems answered correctly.

```python
subjects = ["algebra", "counting_and_probability", "geometry", "intermediate_algebra",
            "number_theory", "prealgebra", "precalculus"]
results = []
for subject in subjects:
    for row in load_dataset("EleutherAI/hendrycks_math", subject, split="test", revision=REVISION):
        output = re.split(r"\$|###|\n", generate(train_prompt + "\n" + row["problem"] + "\nAnswer: $"))[0]
        results.append(is_equiv(output, remove_boxed(last_boxed_only_string(row["solution"]))))
print(sum(results) / len(results))
```
