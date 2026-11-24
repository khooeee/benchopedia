The six rule-generalization conditions each provide eight demonstrations and
a test proof. The [original study](https://proceedings.neurips.cc/paper_files/paper/2023/file/09425891e393e64b0535194a81ba15b7-Paper-Conference.pdf)
explains the format and proof accuracy in Sections 4 and 5.

### 1. Load this example and the checker

Run the following Python snippets from a Benchopedia checkout containing
this benchmark. The key `{{key}}` identifies the held-out rule and the
authors' one-based example number. To rebuild the snapshot from the pinned
archive, run `python3 data/prontoqa-ood/import.py`.

```python
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

key = "{{key}}"
directory = Path("data/prontoqa-ood")
with (directory / "tasks.jsonl").open(encoding="utf-8") as source:
    tasks = [json.loads(line) for line in source]
task = next(row for row in tasks if row["key"] == key)

spec = spec_from_file_location("prontoqa_evaluator", directory / "eval.py")
evaluation = module_from_spec(spec)
spec.loader.exec_module(evaluation)
```

### 2. Generate the proof

Use the eight released demonstrations and the test premises in the message.
The model should follow the demonstrations' controlled sentence format.

```python
def generate(messages):
    raise NotImplementedError("Call your model and return its proof as text.")

prediction = generate(evaluation.messages(task))
```

### 3. Check the proof

The [authors' proof checker](https://github.com/asaparov/prontoqa/blob/0a6412b6fddf46324a1cb96e066dd7b3d89b87d6/run_experiment.py#L1108-L1310)
parses the predicted steps, identifies valid inferences, and checks whether
the target conclusion follows through atomic steps. The grade uses that
strict proof-accuracy result. An unparseable reply scores zero.

```python
verdict, proof = evaluation.grade(task, prediction)
print(int(verdict == "pass"))
```

### Score all six conditions

Report proof accuracy separately for each held-out rule. Each condition
contains exactly 100 test examples.

```python
from collections import Counter

total, hits = Counter(), Counter()
for task in tasks:
    rule = task["key"].removeprefix("prontoqa-ood-").rsplit("-", 1)[0]
    prediction = generate(evaluation.messages(task))
    verdict, proof = evaluation.grade(task, prediction)
    total[rule] += 1
    hits[rule] += verdict == "pass"

assert len(total) == 6 and set(total.values()) == {100}
for rule in sorted(total):
    print(rule, hits[rule] / total[rule])
```
