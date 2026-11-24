Follow the [CLRS-Text paper's exact-match protocol](https://arxiv.org/html/2406.04229) for the final answer and the [official LCS traceback convention](https://github.com/google-deepmind/clrs/blob/d1c2ad7af8437c7536cf329d9cef8fdf93184d9d/clrs/_src/algorithms/dynamic_programming.py#L95-L163).

### Fetch the test artifacts

Use Python 3.12 with PyArrow 19.0.1 from the Benchopedia repository root. Run the code below using `uv run --python 3.12 --with pyarrow==19.0.1 python`. The data reader checks each of the five published Parquet shards before selecting its LCS records.

### Load this task

The key combines the seed file number and one-based source row number. The returned length map contains the original length tag for each task.

```python
import runpy
import sys

sys.path.insert(0, "data/clrs-lcs")
source = runpy.run_path("data/clrs-lcs/import.py")
evaluator = runpy.run_path("data/clrs-lcs/eval.py")
records, lengths = source["load_evaluation"]()
tasks = {task["key"]: task for task in records}

key = "{{key}}"
task = tasks[key]
```

### Generate the traceback matrix

Send the published sequences and initial trace. The instruction asks for the final matrix, with the directions in its upper-right block and the other cells set to -1. Use space-separated entries in each bracketed row and separate rows with a comma and space.

```python
def generate(messages):
    raise NotImplementedError("Call your model here")

reply = generate(evaluator["messages"](task))
```

### Score the reply

Extract the final matrix and compare its text with the published final answer. Matrix contents, punctuation and internal whitespace must match. An unreadable reply earns zero credit.

```python
verdict, matrix = evaluator["grade"](task, reply)
print(matrix, int(verdict == "pass"))
```

### Score the full benchmark

Generate one answer per test record with a fixed model configuration. Group the exact-match outcomes by total input length across the five published seeds. Each length contributes 500 records, with 100 from every seed. Keep repeated cases in their original seed files.

```python
from collections import Counter

correct = Counter()
total = Counter()
for key, task in tasks.items():
    length = lengths[key]
    reply = generate(evaluator["messages"](task))
    verdict, _ = evaluator["grade"](task, reply)
    total[length] += 1
    correct[length] += verdict == "pass"

for length in sorted(total):
    print(length, correct[length] / total[length])
```
