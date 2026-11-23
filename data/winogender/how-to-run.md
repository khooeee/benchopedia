The authors' [Winogender paper, section 4](https://aclanthology.org/N18-2002/)
compares coreference decisions across matched sentences and reports how often
each pronoun is linked to the occupation. Its [instantiation script](https://github.com/rudinger/winogender-schemas/blob/1c7f8b481ad8a234b41e9f76a424d6e856e13f7f/scripts/instantiate.py)
generates the 720 released sentences. The steps below apply those resolution
metrics to a chat model.

### 1. Fetch the sentences

From a Benchopedia checkout, run the importer with Python 3.9 or later. It
fetches the complete sentence file at the commit in `benchmark.json`.

```sh
python3 data/winogender/import.py
```

### 2. Load this task

The key `{{key}}` selects one triplet. Triplets are numbered by first appearance
in the upstream file, using the occupation, participant and intended referent
to match variants.

```python
import json
from pathlib import Path
from runpy import run_path

key = "{{key}}"
folder = Path("data/winogender")
with (folder / "tasks.jsonl").open(encoding="utf-8") as source:
    tasks = [json.loads(line) for line in source]
task = next(row for row in tasks if row["key"] == key)
evaluator = run_path(str(folder / "eval.py"))
```

### 3. Resolve each pronoun

Send the masculine, feminine, and neutral sentences as separate requests.
Each request contains one sentence and asks which mention its pronoun refers
to. The answer choices represent the occupation, the other participant, or
neither listed mention.

```python
def generate(messages):
    raise NotImplementedError("Call your model with these messages and return its answer.")

def resolve_triplet(task, generate):
    outputs = []
    while (messages := evaluator["next_messages"](task, outputs)) is not None:
        outputs.append(generate(messages))
    return outputs

outputs = resolve_triplet(task, generate)
```

### 4. Score it

The intended referent comes from the sentence IDs. A correct resolution
matches that label. The occupation selection and disagreement scores record
the model's choice even when that choice is incorrect.

```python
scores = evaluator["score_responses"](task, outputs)
if scores is None:
    raise ValueError("Each response must select A, B, or C.")
print(scores)
```

### Score the full benchmark

Resolve all 240 triplets and average each score. Each mean covers 240 matched
groups, with 720 model requests in total. For an occupation's gender
difference, subtract its masculine occupation selection rate from its
feminine rate.

```python
from collections import defaultdict
from statistics import mean

scores_by_task = []
differences = defaultdict(list)
for task in tasks:
    scores = evaluator["score_responses"](task, resolve_triplet(task, generate))
    if scores is None:
        raise ValueError(f"{task['key']} requires three valid resolutions")
    scores_by_task.append(scores)
    occupation = task["prompt"].splitlines()[0].removeprefix("A. ")
    differences[occupation].append(scores["occupation-feminine"] - scores["occupation-masculine"])

print({metric: mean(row[metric] for row in scores_by_task) for metric in scores_by_task[0]})
print({occupation: mean(values) for occupation, values in differences.items()})
```

The paper relates the per-occupation differences to estimates in its
[occupational statistics table](https://github.com/rudinger/winogender-schemas/blob/1c7f8b481ad8a234b41e9f76a424d6e856e13f7f/data/occupations-stats.tsv).
For its accuracy analysis, Section 4 calls a case a gotcha when the pronoun
gender runs against the occupation's majority gender for the gold occupation
choice, or matches that majority gender for the gold participant choice.
