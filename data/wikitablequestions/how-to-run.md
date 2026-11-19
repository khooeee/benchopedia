The authors' [evaluator.py](https://github.com/ppasupat/WikiTableQuestions/blob/7d455a5a707b96341ef72aff9428749d443d8aa9/evaluator.py) compares a predicted list of values with the reference answer, using the CoreNLP number and date readings stored in the repository's tagged copy of the data. It is Python 2 code, so the steps below run it in the official `python:2.7` Docker image. It only compares values and runs no model-generated code.

### 1. Fetch the dataset and evaluator

```sh
git clone https://github.com/ppasupat/WikiTableQuestions
git -C WikiTableQuestions checkout 7d455a5a707b96341ef72aff9428749d443d8aa9
docker pull python:2.7
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream example ID. The question is stored with the repository's TSV escapes, and the table is the comma-separated file named in its `context` field.

```python
import csv

key = "{{key}}"
with open("WikiTableQuestions/data/pristine-unseen-tables.tsv", encoding="utf-8", newline="") as f:
    rows = csv.DictReader(f, delimiter="\t", quoting=csv.QUOTE_NONE)
    example = next(row for row in rows if row["id"] == key)
question = example["utterance"].replace(r"\n", "\n").replace(r"\p", "|").replace("\\\\", "\\")
with open(f"WikiTableQuestions/{example['context']}", encoding="utf-8") as f:
    table = f.read()
```

### 3. Generate an answer

The authors publish no prompt for language models. Give the model the question and the table, and have it return its answer as a list of values. The evaluator reads a value that parses as a number as that number, and a value of the form `yyyy-mm-dd` as a date, with `xx` for an unknown field.

```python
def generate(question: str, table: str) -> list[str]:
    raise NotImplementedError("Call your model and return its answer as a list of values.")

answers = generate(question, table)
```

### 4. Score it

The evaluator reads one prediction per line, the example ID followed by one tab-separated item per value, and prints `True` or `False` for each example. Tabs and newlines inside a value would break that format, so the code collapses whitespace, as the evaluator's normalisation does anyway.

```python
import os
import subprocess

with open("prediction.tsv", "w", encoding="utf-8") as f:
    f.write("\t".join([key, *(" ".join(value.split()) for value in answers)]) + "\n")
result = subprocess.run(
    ["docker", "run", "--rm", "-v", f"{os.getcwd()}:/work", "-w", "/work/WikiTableQuestions",
     "python:2.7", "python", "evaluator.py", "../prediction.tsv"],
    capture_output=True, text=True, check=True)
print(result.stdout)  # key, True or False, the reference values, the predicted values
```

### Score the full benchmark

Write one line per question, covering all 4,344 IDs from `nu-0` to `nu-4343`, to `predictions.tsv`; a question with no answer is the ID alone. Run the evaluator from the repository root, where it reads the tagged data in `tagged/data`. Accuracy is the share of questions whose predicted list matches the reference, with the same number of items and every reference item matched; a partly right list earns nothing.

```sh
docker run --rm -v "$PWD:/work" -w /work/WikiTableQuestions python:2.7 \
  python evaluator.py ../predictions.tsv
```
