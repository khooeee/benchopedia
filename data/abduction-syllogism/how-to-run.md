Use the zero-shot methods and numbered replies defined in [Section 4 of the syllogism paper](https://arxiv.org/html/2603.06428v1#S4) and its [worked prompt examples](https://arxiv.org/html/2603.06428v1#S4.T4). The authors publish the labeled tests and define accuracy in the paper. This evaluator applies that metric with its own wording for the directions.

### Fetch both tests

Use Python 3 from the Benchopedia repository root. The importer fetches and verifies the two pinned TSVs.

### Load this task

The key begins with the original three-digit index and ends with `abduction` or `deduction`.

```python
import runpy

source = runpy.run_path("data/abduction-syllogism/import.py")
evaluation = runpy.run_path("data/abduction-syllogism/eval.py")
cases = {task["key"]: (task, content) for task, content in source["load_cases"]()}

key = "{{key}}"
task, content = cases[key]
```

### Generate a choice number

Use the zero-shot prompt for the selected condition and set the generation limit to ten output tokens, as in the original comparison. Supply the model call in `generate`.

```python
def generate(messages, max_tokens):
    raise NotImplementedError("Call your model here")

reply = generate(evaluation["messages"](task), max_tokens=10)
```

### Score the choice

Compare the reply's number with the released answer. A missing or malformed label receives zero credit.

```python
verdict, choice = evaluation["grade"](task, reply)
print(choice, int(verdict == "pass"))
```

### Score the full benchmark

Generate one reply per question under a fixed model configuration. Report accuracy separately for each condition, including the breakdowns by correct-choice number and the authors' content category. [Original accuracy tables](https://arxiv.org/html/2603.06428v1#S4.SS3)

```python
from collections import defaultdict
from statistics import mean

scores = defaultdict(list)
for key, (task, content) in cases.items():
    mode = key.rsplit("-", 1)[1]
    reply = generate(evaluation["messages"](task), max_tokens=10)
    verdict, _ = evaluation["grade"](task, reply)
    correct = int(verdict == "pass")
    reference = evaluation["reference_output"](task)
    for group in ("overall", f"choice {reference}", content):
        scores[mode, group].append(correct)

for (mode, group), values in sorted(scores.items()):
    print(mode, group, mean(values))
```
