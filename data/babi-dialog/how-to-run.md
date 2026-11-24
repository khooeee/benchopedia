Task 1 asks for the next bot response in a simulated restaurant booking.
The [original study](https://arxiv.org/pdf/1605.07683) evaluates the
response against a fixed candidate set and reports both response and
dialog accuracy.

### 1. Load one response turn and the candidates

Run the following Python from a Benchopedia checkout with this benchmark.
The key `{{key}}` gives the split, dialog number, and response turn.
To reproduce the turn snapshot, run `python3 data/babi-dialog/import.py`.
The evaluator loads the 4,212 candidates from the archived candidate file.

```python
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path

key = "{{key}}"
directory = Path("data/babi-dialog")
with (directory / "tasks.jsonl").open(encoding="utf-8") as source:
    tasks = [json.loads(line) for line in source]
task = next(row for row in tasks if row["key"] == key)

spec = spec_from_file_location("babi_dialog_evaluator", directory / "eval.py")
evaluation = module_from_spec(spec)
spec.loader.exec_module(evaluation)
```

### 2. Select the next response

Send the published candidates and the recorded history through the current
customer turn. A line with `<SILENCE>` represents an empty customer turn.
Return the number of one candidate.

```python
def generate(messages):
    raise NotImplementedError("Call your model and return its candidate number as text.")

prediction = generate(evaluation.messages(task))
```

### 3. Score the turn

A turn is correct when the selected candidate equals the reference
response. The adapter also accepts an exact candidate text. An ambiguous
or out-of-range selection scores zero.

```python
verdict, response = evaluation.grade(task, prediction)
print(int(verdict == "pass"))
```

### Report response and dialog accuracy

Score each turn with the recorded history. Count a dialog as correct
only when every response in that dialog is correct. Report both metrics
separately for the standard and out-of-vocabulary splits.

```python
from collections import Counter

turns, correct_turns = Counter(), Counter()
dialog_ok = {}
for task in tasks:
    split, dialog, turn = task["key"].removeprefix("babi-dialog-").split("-")
    prediction = generate(evaluation.messages(task))
    verdict, response = evaluation.grade(task, prediction)
    correct = verdict == "pass"
    turns[split] += 1
    correct_turns[split] += correct
    timeline = (split, dialog)
    dialog_ok[timeline] = dialog_ok.get(timeline, True) and correct

assert turns == {"standard": 5936, "oov": 6020}
for split in sorted(turns):
    dialogs = [correct for (name, dialog), correct in dialog_ok.items() if name == split]
    assert len(dialogs) == 1000
    print(split, correct_turns[split] / turns[split], sum(dialogs) / len(dialogs))
```
