Use the [published question-only input setting](https://github.com/allenai/qasc/blob/c44a320c2bb682d614a675d2ba4be072150db4eb/README.md#no-knowledge-baseline) and the answer accuracy in [the original QASC paper](https://arxiv.org/html/1910.11473).

### Fetch the development release

Use Python 3.12 with PyArrow 19.0.1. From the Benchopedia repository root, run the Python code below with `uv run --python 3.12 --with pyarrow==19.0.1 python`. The importer downloads and verifies AllenAI's pinned development file.

### Load this question

Use the original example ID to select one of the 926 published development records.

```python
import runpy

source = runpy.run_path("data/qasc/import.py")
evaluator = runpy.run_path("data/qasc/eval.py")
tasks = {task["key"]: task for task in source["load_tasks"]()}

key = "{{key}}"
task = tasks[key]
```

### Generate an answer

Give the model the released question and choices. Ask it to identify the answer with one letter from A through H.

```python
def generate(messages):
    raise NotImplementedError("Call your model here")

reply = generate(evaluator["messages"](task))
```

### Score the reply

Give one point when the predicted label equals the released reference. Unreadable replies earn zero credit.

```python
verdict, label = evaluator["grade"](task, reply)
print(label, int(verdict == "pass"))
```

### Score the full benchmark

Generate one reply for each development question with a fixed model configuration and divide the number of correct labels by the total number of questions.

```python
correct = 0
for task in tasks.values():
    reply = generate(evaluator["messages"](task))
    verdict, _ = evaluator["grade"](task, reply)
    correct += verdict == "pass"

print(correct / len(tasks))
```
