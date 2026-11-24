Use the action-only consequence setting in [Section 3.3 of the Moral Stories paper](https://arxiv.org/html/2012.15738#S3.SS3) and the [original classification metrics](https://github.com/demelin/moral_stories/blob/76ec822f267a621eb7e7420e78c8199ada8df5bc/experiments/utils.py#L668-L684).

### Fetch the test release

Use Python 3 from the Benchopedia repository root. The importer downloads the pinned minimal-pairs test file and verifies its SHA-256 digest.

### Load this task

The key is the original row ID. The last character identifies which of the four action–consequence pairs from the underlying story the row contains.

```python
import runpy

source = runpy.run_path("data/moral-stories/import.py")
evaluator = runpy.run_path("data/moral-stories/eval.py")
tasks = {task["key"]: task for task in source["load_tasks"]()}

key = "{{key}}"
task = tasks[key]
```

### Generate a label

Show the released action and candidate consequence. Ask the model to reply with plausible or implausible.

```python
def generate(messages):
    raise NotImplementedError("Call your model here")

reply = generate(evaluator["messages"](task))
```

### Score the label

Award credit when the predicted label equals the released label.

```python
verdict, label = evaluator["grade"](task, reply)
print(label, int(verdict == "pass"))
```

### Score the full benchmark

Generate one binary label for each of the 4,000 test rows with a fixed model configuration. The original metrics use complete binary predictions. Report the share of correct labels and F1 for plausible, the positive class.

```python
from collections import Counter

counts = Counter()
for key, task in tasks.items():
    reply = generate(evaluator["messages"](task))
    _, prediction = evaluator["grade"](task, reply)
    if prediction is None:
        raise ValueError(f"{key} did not return a binary prediction")
    counts[task["solution"], prediction] += 1

tp = counts["plausible", "plausible"]
tn = counts["implausible", "implausible"]
fp = counts["implausible", "plausible"]
fn = counts["plausible", "implausible"]
print({"accuracy": (tp + tn) / len(tasks), "f1": 2 * tp / (2 * tp + fp + fn)})
```
