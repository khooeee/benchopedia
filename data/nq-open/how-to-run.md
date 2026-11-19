NQ-Open is scored as exact-match accuracy. The official scorer is ORQA's [`evaluate_predictions.py`](https://github.com/google-research/language/blob/865fae65f63ef7e6b2989d4ff8b47f61750415a8/language/orqa/evaluation/evaluate_predictions.py), which the [NQ-Open README](https://github.com/google-research-datasets/natural-questions/blob/fb26a3073b1fe636c97302890a27b491d6530130/nq_open/README.md) names for comparing predictions with the `answer` field. A prediction is correct when, after [normalization](https://github.com/google-research/language/blob/865fae65f63ef7e6b2989d4ff8b47f61750415a8/language/orqa/utils/eval_utils.py), it equals any one of the reference answers.

### 1. Fetch the data and the scorer

The scorer lives in Google's large `language` repository, so fetch only its ORQA evaluation code at the pinned commit. It reads files through TensorFlow and parses flags with absl.

```sh
pip install tensorflow absl-py
curl -LO https://raw.githubusercontent.com/google-research-datasets/natural-questions/fb26a3073b1fe636c97302890a27b491d6530130/nq_open/NQ-open.dev.jsonl
git clone --filter=blob:none --no-checkout https://github.com/google-research/language.git google-language
git -C google-language sparse-checkout set language/orqa/utils language/orqa/evaluation
git -C google-language checkout 865fae65f63ef7e6b2989d4ff8b47f61750415a8
```

### 2. Load this task

Benchopedia's key `{{key}}` is `dev-` followed by the question's line number in `NQ-open.dev.jsonl`.

```python
import json

key = "{{key}}"
line_number = int(key.removeprefix("dev-"))
with open("NQ-open.dev.jsonl", encoding="utf-8") as f:
    example = next(json.loads(line) for number, line in enumerate(f, start=1) if number == line_number)
```

### 3. Generate an answer

The model sees only the question, as typed into Google search. It returns one short answer string.

```python
def generate(question: str) -> str:
    raise NotImplementedError("Call your model and return a short answer, a few words at most.")

prediction = generate(example["question"])
```

### 4. Score it

`is_correct` normalizes the prediction and each reference, then checks for an exact match with any of them.

```python
import sys

sys.path.insert(0, "google-language")
from language.orqa.utils import eval_utils

print(eval_utils.is_correct(answers=example["answer"], prediction=prediction, is_regex=False))
```

### Score the full benchmark

Write `predictions.jsonl` with one line per question, `{"question": ..., "prediction": ...}`, using the question text exactly as in `NQ-open.dev.jsonl`, because the scorer matches predictions to references by question. Then run the script. It prints how many questions have no prediction, which count as wrong, and the accuracy over all 3,610 questions.

```sh
cd google-language
python -m language.orqa.evaluation.evaluate_predictions \
    --references_path=../NQ-open.dev.jsonl --predictions_path=../predictions.jsonl
```
