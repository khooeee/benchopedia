Use the [authors' exact-output accuracy rule](https://github.com/i-machine-think/am-i-compositional/blob/4f75bdd78889150dd78e90bbb7ddec840204c159/data/pcfgset/pcfgset/README.md#data-format) and [published string operations](https://github.com/MathijsMul/pcfg-set/blob/99098bd97150671003de60526d884d7c24949944/tasks/default.py).

### Fetch the test files

Run the guide from the Benchopedia repository root with Python 3. The importer downloads the pinned naturalized expressions and targets, checks all four file hashes, and pairs records by line number.

### Load this task

Use the split and one-based line number from the task key to select an expression and its target.

```python
import runpy
import sys

sys.path.insert(0, "data/pcfgset")
source = runpy.run_path("data/pcfgset/import.py")
evaluator = runpy.run_path("data/pcfgset/eval.py")
tasks = {task["key"]: task for task in source["load_tasks"]()}

key = "{{key}}"
task = tasks[key]
```

### Generate the output sequence

Send the original prefix expression plus definitions of the six unary and four binary operations. Ask for the final sequence of space-separated tokens.

```python
def generate(messages):
    raise NotImplementedError("Call your model here")

reply = generate(evaluator["messages"](task))
```

### Score the reply

The evaluator reads the returned token sequence and compares it with the complete target. Credit requires matching each symbol in order.

```python
verdict, output = evaluator["grade"](task, reply)
print(int(verdict == "pass"), output)
```

### Score the full benchmark

Generate an answer for every source expression with a fixed model configuration. Count the fraction of exact matches separately for systematicity and productivity. Keep both occurrences of expressions present in the two tests. Unreadable replies earn zero credit.

```python
from collections import Counter

correct = Counter()
total = Counter()
for key, task in tasks.items():
    split = key.split("-", 1)[0]
    reply = generate(evaluator["messages"](task))
    verdict, _ = evaluator["grade"](task, reply)
    total[split] += 1
    correct[split] += verdict == "pass"

print({split: correct[split] / total[split] for split in ("systematicity", "productivity")})
```
