WinoGrande's data package, fetched by the authors' [download script](https://github.com/allenai/winogrande/blob/727e837f77521ef38bcc56df3b275c8da43f45af/download_winogrande.sh), includes their `eval.py`, which scores predicted option numbers against `dev-labels.lst` as accuracy. The authors publish no prompt for language models; their baselines are fine-tuned classifiers.

### 1. Download the package

Check that the zip is the version this snapshot was imported from.

```sh
curl -LO https://storage.googleapis.com/ai2-mosaic/public/winogrande/winogrande_1.1.zip
echo "3619ab104d8be2977b25c90ff420cb42d491707dcc75362a1e5d22bc082b7318  winogrande_1.1.zip" | shasum -a 256 -c
unzip winogrande_1.1.zip
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream `qID`.

```python
import json

key = "{{key}}"
with open("winogrande_1.1/dev.jsonl", encoding="utf-8") as f:
    row = next(item for item in map(json.loads, f) if item["qID"] == key)
```

### 3. Generate an answer

With no official prompt, this sends the sentence, with its blank `_`, and the two options as this page shows them. Add an instruction if your model needs one.

```python
def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return the number of the option that fills the blank, 1 or 2.")

prediction = generate(f"{row['sentence']}\n\n1. {row['option1']}\n2. {row['option2']}").strip()
```

### 4. Score it

`eval.py` compares option numbers as strings with `dev-labels.lst`, whose line for this question equals the row's `answer`.

```python
print(prediction == row["answer"])
```

### Score the full benchmark

Write `predictions.lst` with one line per question, in `dev.jsonl` order. Each line holds five comma-separated predictions, one for a model trained on each training size from XS to XL; for a single model, repeat its answer five times, as in `2,2,2,2,2`. `eval.py` needs scikit-learn and writes `metrics.json` with an accuracy for each column and the normalized area under that learning curve. When all five columns match, each of these equals the model's accuracy over the 1,267 questions.

```sh
pip install scikit-learn
python3 winogrande_1.1/eval.py --preds_file predictions.lst --labels_file winogrande_1.1/dev-labels.lst
```
