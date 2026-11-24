Use the [authors' zero-shot graph format and integer accuracy](https://github.com/Arthur-Heng/NLGraph/blob/a369f32341c16aaad9d84e7ab835aa3376df1cc3/evaluation/flow.py) for the standard maximum-flow cases.

### Fetch the standard cases

Use Python 3 from the Benchopedia repository root. The reader downloads the 150 Easy and 200 Hard files from the pinned commit and verifies the two source checksums. Each file stores the number of vertices and edges, the directed capacities, the queried source and sink, and the reference flow.

### Load this task

The key preserves the difficulty and original numbered graph file.

```python
import runpy

source = runpy.run_path("data/nlgraph-flow/import.py")
evaluator = runpy.run_path("data/nlgraph-flow/eval.py")
tasks = {task["key"]: task for task in source["load_tasks"]()}

key = "{{key}}"
task = tasks[key]
```

### Generate a flow value

Send the original prose graph and query. Ask the model to reply with the maximum flow as a nonnegative integer.

```python
def generate(messages):
    raise NotImplementedError("Call your model here")

reply = generate(evaluator["messages"](task))
```

### Score the reply

The evaluator accepts the integer on its own or the answer sentence naming the queried endpoints. It awards credit when the value matches the released reference. An unreadable reply earns zero credit.

```python
verdict, value = evaluator["grade"](task, reply)
print(value, int(verdict == "pass"))
```

### Score the full benchmark

Generate one flow value per case with a fixed model configuration. Compare the exact integer and report the fraction correct in each difficulty group.

```python
from collections import Counter

correct = Counter()
total = Counter()
for key, task in tasks.items():
    difficulty = key.split("-", 1)[0]
    reply = generate(evaluator["messages"](task))
    verdict, _ = evaluator["grade"](task, reply)
    total[difficulty] += 1
    correct[difficulty] += verdict == "pass"

print({level: correct[level] / total[level] for level in ("easy", "hard")})
```
