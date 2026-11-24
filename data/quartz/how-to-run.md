Use the question-only setting and answer-choice accuracy from [Sections 5 and 6 of the QuaRTz paper](https://aclanthology.org/D19-1608.pdf#page=3). The test file provides each reference as an A/B answer key.

### Install the data reader

Use Python 3.12 and PyArrow 19.0.1 to read the pinned test Parquet file. From the root of the Benchopedia checkout, run the example code with `uv run --python 3.12 --with pyarrow==19.0.1 python`.

### Load this task

The importer downloads the complete test file at the pinned revision and checks the file hash. The task key is the original row ID.

```python
import runpy

source = runpy.run_path("data/quartz/import.py")
evaluator = runpy.run_path("data/quartz/eval.py")
tasks = {task["key"]: task for task in source["load_tasks"]()}

key = "{{key}}"
task = tasks[key]
```

### Generate an answer

Send the published question and the two choices in their original order. Ask the model for the A or B label.

```python
def generate(messages):
    raise NotImplementedError("Call your model here")

reply = generate(evaluator["messages"](task))
```

### Score the answer

Credit a parsed prediction when its label matches the released answer key.

```python
verdict, prediction = evaluator["grade"](task, reply)
print(prediction, int(verdict == "pass"))
```

### Score the full benchmark

Generate one answer per test record with a fixed model configuration. Report the fraction correct across all 784 records and separately for original and flipped IDs. Unreadable answers earn zero credit. Keep both records in each of the two pairs with identical prompts and opposite labels.

```python
original, flipped = [], []
for key, task in tasks.items():
    reply = generate(evaluator["messages"](task))
    verdict, _ = evaluator["grade"](task, reply)
    group = flipped if key.endswith("-flip") else original
    group.append(int(verdict == "pass"))

all_scores = original + flipped
print({
    "all": sum(all_scores) / len(all_scores),
    "original": sum(original) / len(original),
    "flipped": sum(flipped) / len(flipped),
})
```
