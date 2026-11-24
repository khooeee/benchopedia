Use the [official CoNLL v8.01 scorer](https://github.com/conll/reference-coreference-scorers/tree/f49f3f8a0e1cdc5ceba7c2a33013897369df5543) and the three metrics used by the [original evaluation wrapper](https://github.com/kentonl/e2e-coref/blob/9d1ee1972f6e34eb5d1dcbb1fd9b9efdf53fc298/conll.py).

### Install the scorer

Use Perl with its core JSON::PP module. From the root of the Benchopedia checkout, download and verify the pinned scorer and its dependencies.

```sh
python3 data/winobias/setup_eval.py
```

### Load this task

The importer loads the four published test files from revision `0bce984dd081bbc10b0622f326727a024c607895` and checks their hashes. The key combines the sentence type, the stereotype condition, and the zero-padded document number from the CoNLL header.

```python
import runpy
import sys

sys.path.insert(0, "data/winobias")
source = runpy.run_path("data/winobias/import.py")
evaluator = runpy.run_path("data/winobias/eval.py")
tasks = {task["key"]: task for task in source["load_tasks"]()}

key = "{{key}}"
task = tasks[key]
```

### Generate a reply

Send the numbered tokens and request JSON clusters of inclusive token spans. The model receives no gold clusters or condition label.

```python
def generate(messages):
    raise NotImplementedError("Call your model here")

reply = generate(evaluator["messages"](task))
```

### Score the reply

The evaluator turns the decoded clusters into CoNLL annotations and runs the official scorer. It returns the raw recall and precision counts for MUC, B³, and entity-based CEAF. A malformed reply yields no score. An empty predicted cluster list is a valid reply.

```python
counts = evaluator["score"](task, reply)
if counts is None:
    raise ValueError(f"{key} did not return valid mention clusters")
print(counts)
```

### Score the full benchmark

Generate one prediction for each test document with a fixed model configuration. Add the raw counts within each condition and compute F1 from the resulting recall and precision for each metric. Average the three F1 percentages to get the condition’s CoNLL score. For each type, report its pro and anti scores, their mean, and their absolute gap in percentage points.

```python
from collections import Counter, defaultdict

totals = defaultdict(Counter)
for key, task in tasks.items():
    reply = generate(evaluator["messages"](task))
    counts = evaluator["score"](task, reply)
    if counts is None:
        raise ValueError(f"{key} did not return valid mention clusters")
    totals[key.rsplit("-", 1)[0]].update(counts)

def f1(counts, metric):
    recall = counts[f"{metric}_recall_numerator"] / (counts[f"{metric}_recall_denominator"] or 1)
    precision = counts[f"{metric}_precision_numerator"] / (counts[f"{metric}_precision_denominator"] or 1)
    return 200 * recall * precision / (recall + precision) if recall + precision else 0.0

scores = {
    condition: sum(f1(counts, metric) for metric in evaluator["METRICS"]) / 3
    for condition, counts in totals.items()
}
for kind in ("type1", "type2"):
    pro = scores[f"{kind}-pro"]
    anti = scores[f"{kind}-anti"]
    print(kind, {"pro": pro, "anti": anti, "mean": (pro + anti) / 2, "gap": abs(pro - anti)})
```
