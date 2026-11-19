PIQA's authors publish no scoring script for the labelled validation file. Their [paper](https://arxiv.org/abs/1911.11641) reports accuracy: the fraction of goals for which the model picks the correct one of two solutions. This guide implements that rule on the [validation files](https://github.com/ybisk/ybisk.github.io/tree/21edab439af693b961be2f069e8690a88d3b4e37/piqa/data) this snapshot was imported from.

### 1. Download the data

```sh
curl -LO https://raw.githubusercontent.com/ybisk/ybisk.github.io/21edab439af693b961be2f069e8690a88d3b4e37/piqa/data/valid.jsonl
curl -LO https://raw.githubusercontent.com/ybisk/ybisk.github.io/21edab439af693b961be2f069e8690a88d3b4e37/piqa/data/valid-labels.lst
```

### 2. Load this task

The files have no IDs. Benchopedia's key `{{key}}` is the one-based line number in `valid.jsonl`, and the same line of `valid-labels.lst` holds its label.

```python
import json

key = "{{key}}"
line = int(key.removeprefix("piqa-")) - 1
with open("valid.jsonl", encoding="utf-8") as f:
    row = json.loads(f.readlines()[line])
with open("valid-labels.lst", encoding="utf-8") as f:
    label = f.read().split()[line]
```

### 3. Generate an answer

The authors publish no prompt for language models; their baselines are fine-tuned classifiers. This sends the goal and the two solutions, numbered as this page shows them. Add an instruction if your model needs one.

```python
def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return the number of the better solution, 1 or 2.")

prediction = generate(f"{row['goal']}\n\n1. {row['sol1']}\n2. {row['sol2']}").strip()
```

### 4. Score it

Labels are zero-based: `0` selects solution 1 and `1` selects solution 2.

```python
print(prediction == str(int(label) + 1))
```

### Score the full benchmark

Repeat steps 2 to 4 for all 1,838 lines and report the fraction answered correctly. [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness/blob/v0.4.13/lm_eval/tasks/piqa/piqa.yaml) v0.4.13's `piqa` task scores a copy of the same 1,838 questions differently: it writes the goal after `Question:`, ends with `Answer:`, and picks the solution the model finds more likely, reporting accuracy.

```sh
pip install "lm-eval[hf]==0.4.13"
lm-eval run --model hf --model_args pretrained=YOUR_MODEL --tasks piqa
```
