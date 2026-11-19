The maintainers' [official evaluation script for SQuAD 2.0](https://github.com/rajpurkar/SQuAD-explorer/blob/eee5fdbf62f8613a7812b03419e6b29617b74fd1/evaluate-v2.0.py) scores each answer by exact match and token F1 against the reference answers. An empty answer means the model abstains, and it is the only correct answer to an unanswerable question.

### 1. Fetch the script and the data

The script imports numpy. It is saved under an importable name, and its `__main__` guard keeps an import from running it.

```sh
pip install numpy
curl -L -o evaluate_v2.py https://raw.githubusercontent.com/rajpurkar/SQuAD-explorer/eee5fdbf62f8613a7812b03419e6b29617b74fd1/evaluate-v2.0.py
curl -LO https://raw.githubusercontent.com/rajpurkar/SQuAD-explorer/eee5fdbf62f8613a7812b03419e6b29617b74fd1/dataset/dev-v2.0.json
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream question ID.

```python
import json

key = "{{key}}"
with open("dev-v2.0.json", encoding="utf-8") as f:
    dataset = json.load(f)["data"]
article, paragraph, qa = next(
    (article, paragraph, qa)
    for article in dataset
    for paragraph in article["paragraphs"]
    for qa in paragraph["qas"]
    if qa["id"] == key
)
```

### 3. Generate an answer

The model reads the question and its paragraph. It returns a span of the paragraph, or an empty string to abstain.

```python
def generate(question: str, paragraph: str) -> str:
    raise NotImplementedError("Call your model and return a span of the paragraph, or '' to abstain.")

answer = generate(qa["question"], paragraph["context"])
```

### 4. Score it

`get_raw_scores` takes the best exact match and F1 over the reference answers. When a question has no answers, the only reference is the empty string.

```python
from evaluate_v2 import get_raw_scores

exact, f1 = get_raw_scores([{"paragraphs": [{"qas": [qa]}]}], {key: answer})
print(exact[key], f1[key])  # each between 0 and 1
```

### Score the full benchmark

Write `predictions.json` as one JSON object that maps every question ID to its answer, using `""` to abstain, then run the script. It reports exact match and F1 averaged over all 11,873 questions on a 0 to 100 scale, with `HasAns_` and `NoAns_` figures for answerable and unanswerable questions. Pass `--na-prob-file` with per-question no-answer probabilities to also get the best scores over abstention thresholds.

```sh
python evaluate_v2.py dev-v2.0.json predictions.json
```
