These steps evaluate the seven basic zero-shot test sets in the
[pinned GraphQA release](https://huggingface.co/datasets/baharef/GraphQA/tree/ca8b67f4961e4110c949e81d20b829b6af59cad1).
The [paper](https://openreview.net/pdf?id=IuXR1CCrSi) describes the
task definitions in Appendix A.2.1 and reports accuracy by task type.

### 1. Load one task

Run the Python snippets from a Benchopedia checkout containing
`data/graphqa/`. The key `{{key}}` contains the task type and
the one-based row number in its released JSON file. Use
`python3 data/graphqa/import.py` to reproduce the snapshot.

```python
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

key = "{{key}}"
directory = Path("data/graphqa")
with (directory / "tasks.jsonl").open(encoding="utf-8") as source:
    tasks = [json.loads(line) for line in source]
task = next(row for row in tasks if row["key"] == key)

spec = spec_from_file_location("graphqa_evaluator", directory / "eval.py")
evaluation = module_from_spec(spec)
spec.loader.exec_module(evaluation)
```

### 2. Generate an answer

Send the original graph description and question. The chat adapter
requests an answer in the format for the selected task type.

```python
def generate(messages):
    raise NotImplementedError("Call your model and return its answer as text.")

response = generate(evaluation.messages(task))
```

### 3. Score the answer

Count a matching yes-or-no label, integer, or node set as correct.
The adapter compares node IDs without regard to order and recognizes
`No nodes` as the empty set. Blank or ambiguous replies score zero.

```python
verdict, answer = evaluation.grade(task, response)
print(int(verdict == "pass"))
```

### Score all seven task types

Report the fraction of correct answers for each type over its 500 rows.

```python
from collections import Counter

total, hits = Counter(), Counter()
for task in tasks:
    kind = task["key"].removeprefix("graphqa-").rsplit("-", 1)[0]
    response = generate(evaluation.messages(task))
    verdict, answer = evaluation.grade(task, response)
    total[kind] += 1
    hits[kind] += verdict == "pass"

assert len(total) == 7 and set(total.values()) == {500}
for kind in sorted(total):
    print(kind, hits[kind] / total[kind])
```
