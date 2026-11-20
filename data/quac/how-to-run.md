The authors' [official scorer](https://s3.amazonaws.com/my89public/quac/scorer.py) computes word-level F1 against the reference answers, leaving one reference out at a time. It compares that F1 with the human F1 for the HEQ scores and checks the predicted dialog acts. The scorer is published as an unversioned file, so the steps below pin it by its SHA-256 digest.

### 1. Fetch the scorer and the data

The scorer needs only the standard library, and its `__main__` guard keeps an import from running it.

```sh
curl -LO https://s3.amazonaws.com/my89public/quac/scorer.py
curl -LO https://s3.amazonaws.com/my89public/quac/val_v0.2.json
shasum -a 256 -c <<'EOF'
cd9a391bbc93a6e8c62dbbd0b4945d3f915850a9dd07be80a637d9dabff30f84  scorer.py
09e622916280ba04c9352acb1bc5bbe80f11a2598f6f34e934c51d9e6570f378  val_v0.2.json
EOF
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream question ID; the part before `_q#` names its dialogue. The earlier turns carry the answers the original teacher gave.

```python
import json

key = "{{key}}"
with open("val_v0.2.json", encoding="utf-8") as f:
    data = json.load(f)["data"]
paragraph = next(d["paragraphs"][0] for d in data if d["paragraphs"][0]["id"] == key.split("_q#")[0])
history = []
for qa in paragraph["qas"]:
    if qa["id"] == key:
        break
    history.append((qa["question"], qa["orig_answer"]["text"]))
```

### 3. Generate an answer

The model reads the section text, which ends with `CANNOTANSWER`, the earlier turns and the question. It returns a span copied from the section, or `CANNOTANSWER`, and two dialog acts. The affirmation is `y`, `n` or `x` for neither, and the continuation is `y`, `m` or `n` for follow up, maybe follow up and don't follow up.

```python
def generate(question: str, history: list, section: str) -> tuple:
    raise NotImplementedError("Call your model and return (span, affirmation, continuation).")

span, yesno, followup = generate(qa["question"], history, paragraph["context"])
```

### 4. Score it

```python
from scorer import handle_cannot, leave_one_out, leave_one_out_max

references = handle_cannot([answer["text"] for answer in qa["answers"]])
f1 = leave_one_out_max(span, references, paragraph["context"])
human_f1 = leave_one_out(references)
print("F1:", f1, "in headline F1:", human_f1 >= 0.4, "HEQ:", f1 >= human_f1)
print("affirmation:", yesno == qa["yesno"], "continuation:", followup == qa["followup"])
```

### Score the full benchmark

Write one JSON line per dialogue holding parallel lists `qid`, `best_span_str`, `yesno` and `followup`, covering every question, then run the scorer. The headline F1 averages over the questions whose human F1 is at least 0.4, which `--min_f1` sets. HEQ-Q is the share of those questions where the model matches or beats the human F1. HEQ-D is the share of dialogues where it does so on every counted question. The scorer also prints the unfiltered F1 and the dialog-act accuracies, all on a 0 to 100 scale.

```sh
python scorer.py --val_file val_v0.2.json --model_output predictions.jsonl --o scores.json
```

### Verify with the Benchopedia sweep

The sweep records one JSON reply per question, with the answer span, the
yes/no act, and the follow-up act. It records the unfiltered F1 for every
valid reply and records headline F1 and accuracy metrics for questions with
human F1 of at least 0.4. For the published HEQ-D, group predictions by
dialogue and use the full scorer above. A two-question scratch sweep does
not measure dialogue-level or split-level performance.
