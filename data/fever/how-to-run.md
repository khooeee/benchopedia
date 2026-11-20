The shared task's [fever-scorer](https://github.com/sheffieldnlp/fever-scorer/tree/4801615100fbf6327f8e99b5dbaefe5dd890e869) computes the FEVER score: a claim counts only if the predicted label is right and, unless the label is NOT ENOUGH INFO, the first five predicted evidence sentences include a complete annotated evidence set. A system finds that evidence itself in the authors' processed June 2017 Wikipedia, [wiki-pages.zip](https://fever.ai/download/fever/wiki-pages.zip).

### 1. Install the scorer

The scorer is one module whose only dependency is `six`; it is used here straight from the clone.

```sh
git clone https://github.com/sheffieldnlp/fever-scorer
git -C fever-scorer checkout 4801615100fbf6327f8e99b5dbaefe5dd890e869
pip install six
```

### 2. Load this task

Benchopedia's key `{{key}}` is the claim's upstream `id` in the labelled development split.

```python
import json
import urllib.request

key = "{{key}}"
url = "https://fever.ai/download/fever/shared_task_dev.jsonl"
with urllib.request.urlopen(url) as f:
    instance = next(r for r in map(json.loads, f) if r["id"] == int(key))
```

### 3. Generate a verdict

The system receives only the claim. It returns a label, `SUPPORTS`, `REFUTES` or `NOT ENOUGH INFO`, and its evidence as `[page, sentence]` pairs: the page identifier as written in the Wikipedia archive, such as `Carlos_Santana`, and the sentence number counting from 0.

```python
def generate(claim: str) -> tuple[str, list[list]]:
    raise NotImplementedError("Call your system and return its label and its ranked [page, sentence] evidence.")

instance["predicted_label"], instance["predicted_evidence"] = generate(instance["claim"])
```

### 4. Score it

`fever_score` calls these two functions for each claim, with the shared task's limit of five evidence sentences.

```python
import sys

sys.path.insert(0, "fever-scorer/src")
from fever.scorer import is_correct_label, is_strictly_correct

print({"label_correct": is_correct_label(instance),
       "fever_score": is_strictly_correct(instance, max_evidence=5)})
```

### Score the full benchmark

Predict all 19,998 claims, keep the predictions in the file's order, and pass them with the labelled records to the scorer.

```python
from fever.scorer import fever_score

strict_score, label_accuracy, precision, recall, f1 = fever_score(predictions, actual=records, max_evidence=5)
```

The FEVER score is the fraction of claims that are strictly correct, and label accuracy the fraction with the right label. Evidence precision, recall and F1 are averaged over the claims that are not NOT ENOUGH INFO, where recall credits a claim only when a complete evidence set was retrieved. Official results come from the blind test split, scored by submission; scores on this split are self-reported.

### Verify with the Benchopedia sweep

Run `python3 data/fever/setup_eval.py` to build a local index of the pinned
Wikipedia archive, then run `python3 runner/sweep.py fever --verify-grader`.
The sweep uses a title-search retrieval baseline. It passes the claim and
the top retrieved sentences to the model. The grader checks the original
page and sentence IDs, keeps the five-evidence limit, and records strict
FEVER score, label accuracy, and evidence precision and recall.
