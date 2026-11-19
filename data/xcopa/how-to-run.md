XCOPA is scored as accuracy: the fraction of questions on which a system chooses the labelled alternative, reported for each language and averaged over the eleven. The authors publish the test sets in their [repository](https://github.com/cambridgeltl/xcopa/tree/e2e9d7f105a758ee869cd13e0fe251ef93a29840/data) but no scoring script, so the comparison below is the whole computation.

### 1. Load this task

Benchopedia's key `{{key}}` is the language code and the record's `idx` in that language's test file. The file is fetched from the pinned commit.

```python
import json
import urllib.request

REVISION = "e2e9d7f105a758ee869cd13e0fe251ef93a29840"
key = "{{key}}"
language, number = key.split("-")
url = (f"https://raw.githubusercontent.com/cambridgeltl/xcopa/{REVISION}"
       f"/data/{language}/test.{language}.jsonl")
with urllib.request.urlopen(url) as response:
    records = [json.loads(line) for line in response.read().decode("utf-8").splitlines()]
item = records[int(number)]
assert item["idx"] == int(number)
```

### 2. Generate an answer

The prompt follows Benchopedia's COPA page: the translated premise, COPA's English question for the record's direction, then the two numbered alternatives.

```python
QUESTIONS = {"cause": "What was the CAUSE of this?", "effect": "What happened as a RESULT?"}

def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return the number of the more plausible alternative, 1 or 2.")

prompt = (f"Premise: {item['premise']} {QUESTIONS[item['question']]}\n\n"
          f"Alternative 1: {item['choice1']}\n\nAlternative 2: {item['choice2']}")
prediction = generate(prompt).strip()
```

### 3. Score it

The file records the correct alternative as `label`, 0 for the first and 1 for the second.

```python
print(prediction == str(item["label"] + 1))
```

### Score the full benchmark

Repeat for `idx` 0 to 499 in each of `et`, `ht`, `id`, `it`, `qu`, `sw`, `ta`, `th`, `tr`, `vi`, and `zh`. A language's accuracy is the number of correct answers divided by 500, and the figure on the README's leaderboard is the mean of the eleven accuracies.

lm-evaluation-harness's `xcopa` group scores the same eleven test sets from the Hugging Face dataset `cambridgeltl/xcopa`, but it compares the model's likelihood of each alternative after the premise and a connective chosen from the direction, so it needs log-probabilities rather than a generated answer.
