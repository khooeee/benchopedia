Use the two-label accuracy and reporting groups from the [official HANS evaluator](https://github.com/tommccoy1/hans/blob/7299f6f657089ce06a0f98e7e81f8d0f5b7741ce/evaluate_heur_output.py).

### Fetch the evaluation set

Use Python 3 from the Benchopedia repository root. The data reader downloads the pinned HANS evaluation file and verifies its hash. It retains each row's reporting categories for the full benchmark score.

### Load this task

Select the row by its original pair ID.

```python
import runpy

source = runpy.run_path("data/hans/import.py")
evaluator = runpy.run_path("data/hans/eval.py")
rows, categories = source["load_evaluation"]()
tasks = {task["key"]: task for task in rows}

key = "{{key}}"
task = tasks[key]
```

### Generate an inference label

Send the premise and hypothesis and ask the model whether the premise guarantees the hypothesis. The available labels are entailment and non-entailment.

```python
def generate(messages):
    raise NotImplementedError("Call your model here")

reply = generate(evaluator["messages"](task))
```

### Score the reply

Compare the predicted label with the released binary label. As in the paper, neutral and contradiction map to non-entailment. Unreadable replies earn zero credit.

```python
verdict, answer = evaluator["grade"](task, reply)
print(answer, int(verdict == "pass"))
```

### Score the full benchmark

Generate one label per pair with a fixed model configuration. The authors report accuracy for each heuristic separately for the two gold labels. They also report accuracy by subcase and by template. The example below computes all three reports using the original row metadata.

```python
from collections import Counter

correct = Counter()
total = Counter()
for key, task in tasks.items():
    heuristic, subcase, template = categories[key]
    reply = generate(evaluator["messages"](task))
    verdict, _ = evaluator["grade"](task, reply)
    for group in (("heuristic", heuristic, task["solution"]), ("subcase", subcase), ("template", template)):
        total[group] += 1
        correct[group] += verdict == "pass"

for group in sorted(total):
    print(*group, correct[group] / total[group])
```
