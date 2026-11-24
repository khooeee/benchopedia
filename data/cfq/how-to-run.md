Use the [original CFQ query preprocessing](https://github.com/google-research/google-research/blob/675101293d39a5b88996e58475a026e039a0bdae/cfq/preprocess.py) and the [exact-match evaluation](https://github.com/google-research/google-research/blob/675101293d39a5b88996e58475a026e039a0bdae/cfq/evaluate.py). The three test splits use the same query format.

### Download the release

From the Benchopedia repository root, download the pinned v1.1 archive. The reader streams the dataset inside the archive.

```sh
mkdir -p build/upstream/cfq
curl --fail --location \
  'https://storage.googleapis.com/cfq_dataset/cfq1.1.tar.gz?generation=1584526486399149' \
  --output build/upstream/cfq/cfq1.1.tar.gz
```

Use Python 3.12 with ijson 3.3.0 for the data reader. Run the code below with `uv run --python 3.12 --with ijson==3.3.0 python`.

### Load this task

The data reader verifies the archive hash before streaming the original records and loading the three official split files. The key combines the split name with the zero-padded index of the record in the archive.

```python
from pathlib import Path
import runpy
import sys

sys.path.insert(0, "data/cfq")
source = runpy.run_path("data/cfq/import.py")
evaluator = runpy.run_path("data/cfq/eval.py")
archive = Path("build/upstream/cfq/cfq1.1.tar.gz")
tasks = {task["key"]: task for task in source["load_tasks"](archive)}

key = "{{key}}"
task = tasks[key]
```

### Generate a query

Send the tokenized English question and request a Freebase SPARQL SELECT query. The prompt preserves the original entity placeholders.

```python
def generate(messages):
    raise NotImplementedError("Call your model here")

reply = generate(evaluator["messages"](task))
```

### Score the query

The adapter extracts the query text and applies the baseline's preprocessing. It compares the result with the canonical query, including token and clause order. Scoring is a string comparison.

```python
verdict, canonical_query = evaluator["grade"](task, reply)
print(int(verdict == "pass"), canonical_query)
```

### Score the full benchmark

Generate one query for each test occurrence using a fixed model configuration. Report exact-match accuracy separately for MCD1, MCD2, and MCD3. MCD-MEAN is the arithmetic mean of the three accuracies. Unreadable replies earn zero credit. The catalog's direct prompting uses the published test inputs and references. The original training experiments also used each split's corresponding training data.

```python
from collections import Counter

correct = Counter()
total = Counter()
for key, task in tasks.items():
    split = key.split("-", 1)[0]
    reply = generate(evaluator["messages"](task))
    verdict, _ = evaluator["grade"](task, reply)
    correct[split] += verdict == "pass"
    total[split] += 1

accuracy = {split: correct[split] / total[split] for split in ("mcd1", "mcd2", "mcd3")}
print(accuracy)
print("MCD-MEAN", sum(accuracy.values()) / len(accuracy))
```
