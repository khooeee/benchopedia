CommonsenseQA's [website](https://web.archive.org/web/20200418224329/https://www.tau-nlp.org/commonsenseqa) named AI2's [OpenBookQA evaluator](https://github.com/allenai/aristo-leaderboard/blob/60d5be31b5a7d36f29d13223ece29a8d2bfa8b5f/openbookqa/evaluator/evaluator.py) as its evaluation script. A question earns 1 point when the predicted label matches the answer key, or 1/k when k tied labels include it, and the score is the mean over questions. The authors publish no prompt for language models; their baselines are fine-tuned classifiers.

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
validation = load_dataset("tau/commonsense_qa", split="validation",
                          revision="94630fe30dad47192a8546eb75f094926d47e155")
row = next(item for item in validation if item["id"] == key)
```

### 3. Generate an answer

This sends the question and choices A to E as its task page shows them. Add an instruction if your model needs one.

```python
def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return the letter of its chosen answer, A to E.")

labels, texts = row["choices"]["label"], row["choices"]["text"]
prompt = row["question"] + "\n\n" + "\n".join(f"{label}. {text}" for label, text in zip(labels, texts))
prediction = generate(prompt).strip()
```

### 4. Score it

`calculate_accuracy` takes the answer key for each question ID and a list of predicted labels, more than one only for a tie.

```python
import sys

sys.path.insert(0, "aristo-leaderboard/openbookqa/evaluator")
from evaluator import calculate_accuracy

print(calculate_accuracy({key: row["answerKey"]}, {key: [prediction]}))  # 1.0 when correct
```

### Score the full benchmark

Write `predictions.csv` with one line per question, `question ID,label`, covering all 1,221 validation questions; separate tied labels with `;`. The authors' original validation file supplies the answer keys, with the same IDs and answers as this snapshot. The evaluator writes the mean score as `accuracy` to `metrics.json`. The leaderboard's test answers are not public, so this is a validation score.

```sh
curl -O https://s3.amazonaws.com/commensenseqa/dev_rand_split.jsonl
python3 aristo-leaderboard/openbookqa/evaluator/evaluator.py -qa dev_rand_split.jsonl -p predictions.csv -o metrics.json
```
