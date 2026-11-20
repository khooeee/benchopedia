BillSum's authors report ROUGE-1, ROUGE-2 and ROUGE-L F-scores against the single reference summary. Their repository's [compute_rouge_from_texts.py](https://github.com/FiscalNote/BillSum/blob/f1cbe1c9e1a35a2f7ed3ddedafed54abfc3fac8b/billsum/utils/compute_rouge_from_texts.py) computes them with the `rouge` package, pinned at 0.3.2 in its requirements, and rejects summaries longer than 2,000 characters. That script reads the authors' pre-release file layout, so the steps below call the same package on the published archive.

### 1. Fetch the data and install the scorer

The archive has no version history, so check its SHA-256 digest against `5a55dfb231618d63b25cec4773280a2986d38f53d6d4d39b8256b278edf1110c`.

```sh
curl -L -o billsum_v3.zip "https://drive.usercontent.google.com/download?id=1g89WgFHMRbr4QrvA0ngh26PY081Nv3lx&export=download&confirm=t"
shasum -a 256 billsum_v3.zip
pip install rouge==0.3.2 six
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream `bill_id` in the US test split.

```python
import json
import zipfile

key = "{{key}}"
with zipfile.ZipFile("billsum_v3.zip") as archive, archive.open("us_test_data_final_OFFICIAL.jsonl") as f:
    bill = next(r for r in map(json.loads, f) if r["bill_id"] == key)
```

### 3. Generate a summary

The model receives the bill's `text`; Benchopedia's Task Prompt also gives its `title`. The paper capped generated summaries at 2,000 characters, the length that 90% of reference summaries stay within.

```python
def generate(text: str) -> str:
    raise NotImplementedError("Call your model and return a summary of at most 2,000 characters.")

summary = generate(bill["text"])
```

### 4. Score it

```python
from rouge import Rouge

if len(summary) > 2000:
    raise ValueError("The authors' script rejects summaries over 2,000 characters.")
scores = Rouge().get_scores([bill["summary"]], [summary])[0]
print({metric: scores[metric]["f"] for metric in ("rouge-1", "rouge-2", "rouge-l")})
```

### Score the full benchmark

Summarize all 3,269 bills. Align the two lists by bill ID and give the reference
list first, as the authors' script does. Use `avg=True` for the mean of the
per-bill scores.

```python
averages = Rouge().get_scores(references, summaries, avg=True)
print({metric: averages[metric]["f"] for metric in ("rouge-1", "rouge-2", "rouge-l")})
```

The reported scores are those mean F-scores, as the authors' script prints them. The paper names no ROUGE configuration, and longer summaries raise recall at the expense of precision, so compare systems only with the same implementation and similar output lengths.
