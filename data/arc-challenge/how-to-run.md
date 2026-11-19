AI2 scored ARC with its [leaderboard evaluator](https://github.com/allenai/aristo-leaderboard/blob/60d5be31b5a7d36f29d13223ece29a8d2bfa8b5f/arc/evaluator/evaluator.py), which applies the [paper](https://arxiv.org/abs/1803.05457)'s rubric: a question earns 1 point when the predicted label is correct, or 1/k when a k-way tie includes the correct label, and the score is the mean over questions. The authors publish no prompt for language models.

### 1. Install the evaluator

```sh
pip install datasets
git clone https://github.com/allenai/aristo-leaderboard
git -C aristo-leaderboard checkout 60d5be31b5a7d36f29d13223ece29a8d2bfa8b5f
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream question ID. This loads the dataset revision the snapshot was imported from.

```python
from datasets import load_dataset

key = "{{key}}"
test = load_dataset("allenai/ai2_arc", "ARC-Challenge", split="test",
                    revision="210d026faf9955653af8916fad021475a3f00453")
row = next(item for item in test if item["id"] == key)
```

### 3. Generate an answer

This sends the question and its labelled choices as this page shows them. Some questions label their choices 1 to 4 rather than A to D, and the model should answer with the label. Add an instruction if your model needs one.

```python
def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return the label of its chosen answer, such as A or 1.")

labels, texts = row["choices"]["label"], row["choices"]["text"]
prompt = row["question"] + "\n\n" + "\n".join(f"{label}. {text}" for label, text in zip(labels, texts))
prediction = generate(prompt).strip()
```

### 4. Score it

`calculate_accuracy` takes the reference label for each question ID and a list of predicted labels, more than one only for a tie.

```python
import sys

sys.path.insert(0, "aristo-leaderboard/arc/evaluator")
from evaluator import calculate_accuracy

print(calculate_accuracy({key: row["answerKey"]}, {key: [prediction]}))  # 1.0 when correct
```

### Score the full benchmark

Write `predictions.csv` with one line per question, `question ID,label`, covering all 1,172 Challenge test questions; separate tied labels with `;`. Then run the evaluator against the Challenge answer file in the same repository. It writes the mean score as `accuracy` to `metrics.json`.

```sh
python3 aristo-leaderboard/arc/evaluator/evaluator.py -qa aristo-leaderboard/arc/data-challenge/question-answers.jsonl -p predictions.csv -o metrics.json
```
