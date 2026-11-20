BLiMP scores a language model by the probabilities it assigns, not by text it generates: a pair counts as correct when the model gives the acceptable sentence a higher probability than the unacceptable one. The authors ran their GPT-2 and Transformer-XL experiments with scripts in the [`blimp-and-npi` branch of jiant](https://github.com/nyu-mll/jiant/tree/244c9d895236c3446c4c36060283645a57a3175a/scripts/blimp), which need jiant's own setup. The steps below apply the paper's rule with Python's standard library and a scoring function for your model.

### 1. Load this task

Benchopedia's key `{{key}}` joins the paradigm's identifier, which is its file name in `data/`, and the pair number, which is the record's `pairID` and its zero-based line in that file.

```python
import json
import urllib.request

key = "{{key}}"
paradigm, pair = key.rsplit("-", 1)
URL = f"https://raw.githubusercontent.com/alexwarstadt/blimp/3e56b06fcabca9b30822fc66435fca6b1aa40bb1/data/{paradigm}.jsonl"
with urllib.request.urlopen(URL) as response:
    records = [json.loads(line) for line in response.read().decode("utf-8").splitlines()]
record = records[int(pair)]
assert record["pairID"] == pair
```

### 2. Score both sentences

The paper's main method compares the total log probability of each full sentence, with no prompt or context.

```python
def log_probability(sentence: str) -> float:
    raise NotImplementedError("Return your model's total log probability of the sentence.")

good = log_probability(record["sentence_good"])
bad = log_probability(record["sentence_bad"])
```

### 3. Score it

The pair is correct when the acceptable sentence is more probable.

```python
print(good > bad)
```

### Score the full benchmark

Overall accuracy is the proportion of the 67,000 pairs that are correct. The paper also reports accuracy for each paradigm, from the record's `UID`, and for each of its 12 phenomena. The files' `linguistics_term` field gives the phenomenon, though it labels the two s-selection paradigms separately from argument structure.

```python
LISTING = "https://api.github.com/repos/alexwarstadt/blimp/contents/data?ref=3e56b06fcabca9b30822fc66435fca6b1aa40bb1"
with urllib.request.urlopen(LISTING) as response:
    names = [entry["name"] for entry in json.loads(response.read()) if entry["name"].endswith(".jsonl")]
correct = total = 0
for name in names:
    url = f"https://raw.githubusercontent.com/alexwarstadt/blimp/3e56b06fcabca9b30822fc66435fca6b1aa40bb1/data/{name}"
    with urllib.request.urlopen(url) as response:
        for record in map(json.loads, response.read().decode("utf-8").splitlines()):
            correct += log_probability(record["sentence_good"]) > log_probability(record["sentence_bad"])
            total += 1
print(correct / total)
```
