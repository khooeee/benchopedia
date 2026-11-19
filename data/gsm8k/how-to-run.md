The authors' [grade-school-math](https://github.com/openai/grade-school-math/tree/3101c7d5072418e28b9008a6636bde82a006892c) repository holds the test file and the example grader in `grade_school_math/dataset.py`. `is_correct` reads the number after `####` in a completion, removes commas, and compares it as a string with the reference answer's number.

### 1. Fetch the data and grader

```sh
git clone https://github.com/openai/grade-school-math
git -C grade-school-math checkout 3101c7d5072418e28b9008a6636bde82a006892c
pip install torch  # dataset.py imports torch at module level
```

### 2. Load this task

Benchopedia's key `{{key}}` holds the problem's one-based line number in the pinned `test.jsonl`. The repository is not an installable package, so put its folder on the import path.

```python
import sys

sys.path.insert(0, "grade-school-math/grade_school_math")
from dataset import extract_answer, is_correct, read_jsonl

key = "{{key}}"
problems = read_jsonl("grade-school-math/grade_school_math/data/test.jsonl")
problem = problems[int(key.removeprefix("test-")) - 1]
```

### 3. Generate a solution

The authors fine-tuned their models on the training split, so a model sees the question followed by a newline, as `get_examples` formats it, and writes a worked solution whose last line is `#### ` and the final number. Instruct or prompt other models to end the same way.

```python
def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return a worked solution ending in '#### <answer>'.")

completion = generate(problem["question"] + "\n")
```

### 4. Score it

`is_correct` extracts the final number from both texts and requires them to match exactly. A completion without `#### ` followed by a number yields `[invalid]` and counts as wrong.

```python
print(extract_answer(completion), is_correct(completion, problem))
```

### Score the full benchmark

The repository has no batch scorer. Generate one completion for each of the 1,319 test problems; accuracy is the fraction that `is_correct` accepts. The paper also reports verifier-based selection, where a trained verifier picks one of many sampled solutions per problem before the same check.

```python
completions = [generate(p["question"] + "\n") for p in problems]
print(sum(map(is_correct, completions, problems)) / len(problems))
```
