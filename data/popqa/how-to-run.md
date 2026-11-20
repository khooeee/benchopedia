The authors evaluate models with [`run_model.py`](https://github.com/AlexTMallen/adaptive-retrieval/blob/8172ab04794a1651488207c230286b0b3786d736/run_model.py), which needs PyTorch, Transformers and, for GPT-3, OpenAI's retired completions API. The steps below reproduce its zero-shot setting, the one the paper used for GPT-3, and its correctness test with Python's standard library and a generation function for your model.

### 1. Load this task

Benchopedia's key `{{key}}` is the question's `id` in the data file.

```python
import csv
import io
import json
import urllib.request

key = "{{key}}"
URL = "https://raw.githubusercontent.com/AlexTMallen/adaptive-retrieval/8172ab04794a1651488207c230286b0b3786d736/data/popQA.tsv"
with urllib.request.urlopen(URL) as response:
    rows = list(csv.DictReader(io.StringIO(response.read().decode("utf-8"), newline=""), delimiter="\t"))
row = next(row for row in rows if row["id"] == key)
```

### 2. Generate the model's answer

The script formats each question as `Q: <question> A:`, generates at most 15 tokens greedily, and keeps the first line of the continuation, after dropping a leading blank line.

```python
def generate(prompt: str, max_new_tokens: int = 15) -> str:
    raise NotImplementedError("Return your model's greedy continuation of the prompt.")

def predict(question):
    pred = generate(f"Q: {question} A:")
    if pred.startswith("\n\n"):
        pred = pred[2:]
    return pred.split("\n")[0]

pred = predict(row["question"])
```

### 3. Score it

The prediction is correct when any accepted answer, as written, lowercased, or capitalized, appears anywhere in it.

```python
def is_correct(row, pred):
    possible_answers = json.loads(row["possible_answers"])
    return any(pa in pred or pa.lower() in pred or pa.capitalize() in pred for pa in possible_answers)

print(is_correct(row, pred))
```

### Score the full benchmark

Accuracy is the proportion of the 14,267 questions answered correctly. The paper also reports it for each relationship type, the row's `prop`, and against the subject's monthly Wikipedia page views, `s_pop`. Run with `--n_examples 0`, the script matches the steps above; its default instead puts 15 solved examples before each question, one from each other relationship type, as the paper did for GPT-Neo and OPT.

```python
correct = sum(is_correct(row, predict(row["question"])) for row in rows)
print(correct / len(rows))
```
