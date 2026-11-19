BoolQ's authors publish no scoring script for the labelled development set. Their [paper](https://arxiv.org/abs/1905.10044) reports accuracy: the fraction of questions where the model's yes or no matches the reference answer. This guide implements that rule on the dataset revision this snapshot was imported from.

### 1. Install the loader

```sh
pip install datasets
```

### 2. Load this task

The dataset has no question IDs. Benchopedia's key `{{key}}` is the question's one-based row number in the pinned validation split, which holds the authors' development set.

```python
from datasets import load_dataset

key = "{{key}}"
validation = load_dataset("google/boolq", split="validation",
                          revision="35b264d03638db9f4ce671b711558bf7ff0f80d5")
row = validation[int(key.removeprefix("boolq-")) - 1]
```

### 3. Generate an answer

The authors publish no prompt for language models; their baselines are fine-tuned classifiers. This sends the question and passage as its task page shows them. Add an instruction if your model needs one.

```python
def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return yes or no.")

prediction = generate(row["question"] + "\n\n" + row["passage"]).strip().lower()
```

### 4. Score it

The row's `answer` is `True` for yes and `False` for no.

```python
print(prediction == ("yes" if row["answer"] else "no"))
```

### Score the full benchmark

Repeat steps 2 to 4 for all 3,270 rows and report the fraction answered correctly. [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness/blob/v0.4.13/lm_eval/tasks/super_glue/boolq/default.yaml) v0.4.13's `boolq` task scores SuperGLUE's copy of this 3,270-question development set, whose passages begin with the article title. It ends each prompt with `Question:`, the question, `?` and `Answer:`, and picks whichever of no and yes the model finds more likely, reporting accuracy.

```sh
pip install "lm-eval[hf]==0.4.13"
lm-eval run --model hf --model_args pretrained=YOUR_MODEL --tasks boolq
```
