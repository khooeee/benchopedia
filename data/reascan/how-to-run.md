These steps run and score the two syntax conditions from the
[ReaSCAN v1.1 release](https://reascan.github.io/). The [paper](https://datasets-benchmarks-proceedings.neurips.cc/paper_files/paper/2021/file/2838023a778dfaecdc212708f721b788-Paper-round1.pdf)
describes C1 and C2 in Section 6.4 and reports exact match in Table 3.

### 1. Load this example

Run the Python snippets from a Benchopedia checkout containing this
benchmark. The key `{{key}}` gives the condition and one-based row
number in the released test file. Run `python3 data/reascan/import.py` to
rebuild the snapshot using the needed ranges of the official archive.
If you have a local copy, pass `--archive /path/to/ReaSCAN-v1.1.zip`.

```python
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

key = "{{key}}"
directory = Path("data/reascan")
with (directory / "tasks.jsonl").open(encoding="utf-8") as source:
    tasks = [json.loads(line) for line in source]
task = next(row for row in tasks if row["key"] == key)

spec = spec_from_file_location("reascan_evaluator", directory / "eval.py")
evaluation = module_from_spec(spec)
spec.loader.exec_module(evaluation)
```

### 2. Generate an action sequence

Send the command, the text grid state, and the movement rules. The
message describes the [authors' simulator](https://github.com/frankaging/Reason-SCAN/blob/1e6726aab70c915a3d3068bed77ae255feeaf6f1/code/dataset/world.py#L608-L775),
including the preferred route, object movement, and adverbs. Return
the actions separated by commas.

```python
def generate(messages):
    raise NotImplementedError("Call your model and return its actions as text.")

prediction = generate(evaluation.messages(task))
```

### 3. Score the sequence

The [original predictor](https://github.com/frankaging/Reason-SCAN/blob/1e6726aab70c915a3d3068bed77ae255feeaf6f1/code/models/seq2seq/predict.py#L37-L50)
marks a prediction correct when every action matches in the same order.
The adapter parses the listed actions and compares their sequence.
A reply outside the action format scores zero.

```python
verdict, actions = evaluation.grade(task, prediction)
print(int(verdict == "pass"))
```

### Score both syntax conditions

Report C1 and C2 accuracy separately over the complete test sets.

```python
from collections import Counter

total, hits = Counter(), Counter()
for task in tasks:
    condition = task["key"].split("-")[1]
    prediction = generate(evaluation.messages(task))
    verdict, actions = evaluation.grade(task, prediction)
    total[condition] += 1
    hits[condition] += verdict == "pass"

assert total == {"c1": 8375, "c2": 8003}
for condition in sorted(total):
    print(condition, hits[condition] / total[condition])
```
