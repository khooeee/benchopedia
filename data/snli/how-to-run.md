SNLI has no official scoring script or harness. The [paper](https://arxiv.org/abs/1508.05326) scores three-way classification accuracy against each pair's `gold_label`, and the readme in the [SNLI 1.0 archive](https://archive.nyu.edu/handle/2451/41728) says to leave out pairs with no majority label; the steps below apply that rule in a few lines of Python.

### 1. Fetch the data

The archive has no version history, so check its SHA-256 digest against `afb3d70a5af5d8de0d9d81e2637e0fb8c22d1235c2749d83125ca43dab0dbd3e`.

```sh
curl -LO https://archive.nyu.edu/bitstream/2451/41728/2/snli_1.0.zip
shasum -a 256 snli_1.0.zip
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream `pairID` in the test split.

```python
import json
import zipfile

key = "{{key}}"
with zipfile.ZipFile("snli_1.0.zip") as archive, archive.open("snli_1.0/snli_1.0_test.jsonl") as f:
    pair = next(r for r in map(json.loads, f) if r["pairID"] == key)
```

### 3. Generate a label

The model receives the premise, `sentence1`, and the hypothesis, `sentence2`. The readme warns that `captionID` and `pairID` carry clues to the label, so keep them, like the annotator labels, out of the input. SNLI fixes no prompt for language models; Benchopedia's Task Prompt adds one question after the two sentences.

```python
def generate(premise: str, hypothesis: str) -> str:
    raise NotImplementedError("Call your model and return 'entailment', 'neutral' or 'contradiction'.")

prediction = generate(pair["sentence1"], pair["sentence2"])
```

### 4. Score it

The gold label is the one most annotators chose; where none won a majority it is `-`, and the pair does not count.

```python
if pair["gold_label"] == "-":
    print("No majority label: this pair is left out of accuracy.")
else:
    print({"gold_label": pair["gold_label"], "prediction": prediction, "correct": prediction == pair["gold_label"]})
```

### Score the full benchmark

Label all 10,000 test pairs and count the correct ones among the 9,824 that have a gold label. Accuracy is that count divided by 9,824; since the labels ship with the split, every SNLI result is self-reported.
