The authors' [PAL evaluation script](https://github.com/reasoning-machines/pal/blob/f81ca2a9777f002f98a6b4d0f10b61bd5c8feb02/scripts/gsm_eval.py)
compares the computed numeric result with the target. The steps below use
that comparison with a model that returns a number directly.

### 1. Load this problem

Benchopedia's key `{{key}}` contains the one-based line number of the problem
in the pinned author release. Use Python 3.9 or later.

```python
import json
from urllib.request import urlopen

key = "{{key}}"
revision = "960448f73503112d4226baeb8eb41d3fb5ae2506"
url = (f"https://huggingface.co/datasets/reasoning-machines/gsm-hard/"
       f"resolve/{revision}/gsmhardv2.jsonl")
with urlopen(url, timeout=60) as response:
    problems = [json.loads(line) for line in response]
problem = problems[int(key.removeprefix("gsm-hard-")) - 1]
```

### 2. Generate a numeric answer

Send the original problem text and request a numeric reply.

```python
def generate(prompt):
    raise NotImplementedError("Call your model and return its numeric answer as text.")

def prompt_for(problem):
    return problem["input"] + "\n\nUse the quantities as given. Reply with only the final number, including a minus sign if needed."

prediction = generate(prompt_for(problem))
```

### 3. Score it

Parse the numeric reply and use the evaluation script's absolute error
threshold of 0.001. The comparator accepts differences strictly below
the threshold.

```python
import math
import re

number = re.compile(
    r"[+-]?(?:(?:[0-9]+|[0-9]{1,3}(?:,[0-9]{3})+)(?:\.[0-9]*)?|\.[0-9]+)"
    r"(?:[eE][+-]?[0-9]+)?"
)

def correct(prediction, target):
    label = prediction.strip()
    if not number.fullmatch(label):
        return False
    value = float(label.replace(",", ""))
    return math.isfinite(value) and abs(value - target) < 1e-3

print(correct(prediction, problem["target"]))
```

### Score the full benchmark

Repeat on all 1,319 problems. Report the fraction whose numeric responses
meet the threshold.

```python
assert len(problems) == 1319
hits = sum(correct(generate(prompt_for(problem)), problem["target"])
           for problem in problems)
print(hits / len(problems))
```
