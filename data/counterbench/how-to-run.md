The [original study](https://arxiv.org/html/2502.11008v2#S3) grades a
response by whether it gives the correct yes-or-no answer. These steps
use the study's standard prompting setting with the released context
and question.

### 1. Load this question

The key `{{key}}` encodes the source file and the original question ID.

```python
import json
from urllib.request import urlopen

key = "{{key}}"
revision = "c6225dfa00b7a89ccfeae67797b9a6d80e48e44c"
base = f"https://huggingface.co/datasets/CounterBench/CounterBench/resolve/{revision}"
files = {
    "alpha": "data_balanced_alpha_V1.json",
    "backdoor": "data_balanced_backdoor_V2.json",
}

def load_group(group):
    with urlopen(f"{base}/{files[group]}", timeout=60) as response:
        return json.load(response)

_, group, question_id = key.split("-")
rows = load_group(group)
question = next(row for row in rows if row["question_id"] == str(int(question_id)))
```

### 2. Generate a reply

Send the released background and question together. Use a temperature
of zero when your model supports it.

```python
def generate(prompt, temperature):
    raise NotImplementedError("Call your model and return its answer as text.")

def prompt_for(row):
    return row["given_info"] + "\n\n" + row["question"] + "\n\nReply with one word, Yes or No."

prediction = generate(prompt_for(question), temperature=0)
```

### 3. Score the reply

Count one point for a matching label. The adapter ignores letter case
and allows a final period. Ambiguous or empty replies score zero.

```python
import re

answer = re.compile(r"(yes|no)\.?", re.IGNORECASE)

def correct(prediction, reference):
    match = answer.fullmatch(prediction.strip())
    return match is not None and match.group(1).lower() == reference

print(int(correct(prediction, question["answer"])))
```

### Score the full release

Load both files and report accuracy overall and for each of the five
question types.

```python
from collections import Counter

total, hits = Counter(), Counter()
for group in files:
    for question in load_group(group):
        kind = question["type"]
        prediction = generate(prompt_for(question), temperature=0)
        total[kind] += 1
        hits[kind] += correct(prediction, question["answer"])

assert len(total) == 5 and sum(total.values()) == 1200
print("Overall", sum(hits.values()) / sum(total.values()))
for kind in sorted(total):
    print(kind, hits[kind] / total[kind])
```
