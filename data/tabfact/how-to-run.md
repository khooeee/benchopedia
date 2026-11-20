TabFact's paper scores accuracy: a statement counts as correct when the predicted label, entailed (1) or refuted (0), matches its label. The [Table-Fact-Checking repository](https://github.com/wenhuchen/Table-Fact-Checking/tree/2ab782ba42b5808076ac91fec846473aa5315a79) holds code for the authors' own Table-BERT and latent-program models rather than a general scorer, so the steps below apply the paper's rule with Python's standard library and a generation function for your model.

### 1. Load this task

Benchopedia's key `{{key}}` joins the table's file name in `data/all_csv`, without `.html.csv`, and the statement's zero-based position in that table's list in the test file.

```python
import json
import urllib.request

BASE = "https://raw.githubusercontent.com/wenhuchen/Table-Fact-Checking/2ab782ba42b5808076ac91fec846473aa5315a79"

def fetch(path):
    with urllib.request.urlopen(f"{BASE}/{path}") as response:
        return response.read().decode("utf-8")

key = "{{key}}"
stem, index = key.rsplit("-", 1)
table_id = f"{stem}.html.csv"
examples = json.loads(fetch("tokenized_data/test_examples.json"))
statements, labels, caption = examples[table_id]
statement, label = statements[int(index)], labels[int(index)]
table = fetch(f"data/all_csv/{table_id}").replace("\r\n", "\n").rstrip("\n")
```

### 2. Generate the model's label

The table file separates the cells of each row with `#`. Give the model the caption, the table and the statement, and read its answer as 1 for entailed or 0 for refuted.

```python
def generate(caption: str, table: str, statement: str) -> int:
    raise NotImplementedError("Return 1 if your model judges the statement entailed by the table, else 0.")

prediction = generate(caption, table, statement)
```

### 3. Score it

```python
print(prediction == label)
```

### Score the full benchmark

Accuracy is the proportion of the 12,779 test statements labelled correctly. The paper also reports it for the simple and complex parts of the test set and for a small test set, whose tables are listed in `data/simple_test_id.json`, `data/complex_test_id.json` and `data/small_test_id.json`.

```python
correct = total = 0
for table_id, (statements, labels, caption) in examples.items():
    table = fetch(f"data/all_csv/{table_id}").replace("\r\n", "\n").rstrip("\n")
    for statement, label in zip(statements, labels):
        correct += generate(caption, table, statement) == label
        total += 1
print(correct / total)
```
