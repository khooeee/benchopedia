The authors' [hotpot_evaluate_v1.py](https://github.com/hotpotqa/hotpot/blob/3635853403a8735609ee997664e1528f4480762a/hotpot_evaluate_v1.py) scores the answer by exact match and F1, scores the supporting facts as a set of sentences, and combines the two into joint scores.

### 1. Fetch the script and the data

The script imports `ujson`, and its `__main__` guard keeps an import from running it. The authors' download host no longer resolves, so the development file comes from the Internet Archive's copy of their link, checked against the digest Benchopedia imported.

```sh
pip install ujson
curl -LO https://raw.githubusercontent.com/hotpotqa/hotpot/3635853403a8735609ee997664e1528f4480762a/hotpot_evaluate_v1.py
curl -L -o hotpot_dev_distractor_v1.json "https://web.archive.org/web/20260310132809id_/http://curtis.ml.cmu.edu/datasets/hotpot/hotpot_dev_distractor_v1.json"
echo "4e9ecb5c8d3b719f624d66b60f8d56bf227f03914f5f0753d6fa1b359d7104ea  hotpot_dev_distractor_v1.json" | shasum -a 256 -c
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream `_id`.

```python
import json

key = "{{key}}"
with open("hotpot_dev_distractor_v1.json", encoding="utf-8") as f:
    record = next(r for r in json.load(f) if r["_id"] == key)
```

### 3. Generate an answer and supporting facts

In the distractor setting the model reads the question and the record's paragraphs, each a `[title, sentences]` pair. It returns the answer, or yes or no, and the supporting facts as `[title, sentence index]` pairs, counting sentences from zero.

```python
def generate(question: str, context: list) -> tuple:
    raise NotImplementedError("Call your model and return (answer, [[title, sentence_index], ...]).")

answer, supporting_facts = generate(record["question"], record["context"])
```

### 4. Score it

The official `eval` reads a prediction file and a gold file. Given only this question, it prints its answer, supporting-fact and joint scores, each from 0 to 1.

```python
from hotpot_evaluate_v1 import eval as hotpot_eval

with open("prediction.json", "w", encoding="utf-8") as f:
    json.dump({"answer": {key: answer}, "sp": {key: supporting_facts}}, f)
with open("gold.json", "w", encoding="utf-8") as f:
    json.dump([record], f)
hotpot_eval("prediction.json", "gold.json")  # prints em, f1, sp_em, sp_f1, joint_em, joint_f1, ...
```

### Score the full benchmark

Write one prediction file whose `answer` and `sp` objects cover all 7,405 questions, then run the script with the prediction file first. Every metric is averaged over the questions. A question missing from `answer` or `sp` scores zero for that part and for the joint scores.

```sh
python hotpot_evaluate_v1.py predictions.json hotpot_dev_distractor_v1.json
```

### Verify with the Benchopedia sweep

The evaluator numbers each source paragraph's sentences using offsets generated
by the importer from the pinned split. It asks for a JSON answer and supporting
fact pairs and reports all twelve per-question metrics from the official scorer.
It keeps the upstream annotation for the one question whose gold fact names a
sentence outside its paragraph.
