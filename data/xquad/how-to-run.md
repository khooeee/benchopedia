The XQuAD authors score every language with the official SQuAD v1.1 evaluation script, [evaluate-v1.1.py](https://github.com/allenai/bi-att-flow/blob/498c8026d92a8bcf0286e2d216d092d444d02d76/squad/evaluate-v1.1.py), which their [README](https://github.com/google-deepmind/xquad/blob/7d30520c717524000f0d9d2f9c10a069acd9d285/README.md#training-and-evaluation) links to. It reports exact match and token F1 against the reference answer, after English-specific normalisation.

### 1. Fetch the script and the data

The script needs only the standard library. It is saved under an importable name, and its `__main__` guard keeps an import from running it.

```sh
curl -L -o evaluate_v1_1.py https://raw.githubusercontent.com/allenai/bi-att-flow/498c8026d92a8bcf0286e2d216d092d444d02d76/squad/evaluate-v1.1.py
for lang in ar de el en es hi ro ru th tr vi zh; do
  curl -LO "https://raw.githubusercontent.com/google-deepmind/xquad/7d30520c717524000f0d9d2f9c10a069acd9d285/xquad.$lang.json"
done
```

### 2. Load this task

Benchopedia's key `{{key}}` is the language code, a hyphen, and the upstream question ID, which repeats across the twelve language files.

```python
import json

key = "{{key}}"
language, question_id = key.split("-", 1)
with open(f"xquad.{language}.json", encoding="utf-8") as f:
    dataset = json.load(f)["data"]
paragraph, qa = next(
    (paragraph, qa)
    for article in dataset
    for paragraph in article["paragraphs"]
    for qa in paragraph["qas"]
    if qa["id"] == question_id
)
```

### 3. Generate an answer

The model reads the question and its paragraph, both in the file's language, and returns a span of the paragraph.

```python
def generate(question: str, paragraph: str) -> str:
    raise NotImplementedError("Call your model and return a span of the paragraph.")

answer = generate(qa["question"], paragraph["context"])
```

### 4. Score it

```python
from evaluate_v1_1 import exact_match_score, f1_score, metric_max_over_ground_truths

references = [reference["text"] for reference in qa["answers"]]
print(metric_max_over_ground_truths(exact_match_score, answer, references),
      metric_max_over_ground_truths(f1_score, answer, references))  # True or False, then F1 from 0 to 1
```

### Score the full benchmark

For each language, write `predictions.<lang>.json` as one JSON object that maps every question ID in that file to its answer, and run the script. It prints exact match and F1 averaged over the language's 1,190 questions on a 0 to 100 scale. XQuAD results are reported per language and as the average across languages.

```sh
python evaluate_v1_1.py xquad.ar.json predictions.ar.json
```
