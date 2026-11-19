The authors' [evaluate.py](https://github.com/hendrycks/test/blob/4450500f923c49f1fb1dd3d99108a0bd9717b660/evaluate.py) shows the model five answered examples from the same subject's dev split, then this question ending in `Answer:`. It does not parse generated text: it takes the answer letter the model scores highest as the next token, and reports accuracy.

### 1. Install the loader

```sh
pip install datasets
```

### 2. Load this task

Benchopedia's key `{{key}}` is the subject plus the question's one-based row number in the all/test split of the dataset revision this snapshot was imported from. The subject's dev split holds the authors' five examples, in their order.

```python
from datasets import load_dataset

REVISION = "c30699e8356da336a370243923dbaf21066bb9fe"
key = "{{key}}"
subject, _, number = key.rpartition("-test-")
row = load_dataset("cais/mmlu", "all", split="test", revision=REVISION)[int(number) - 1]
assert row["subject"] == subject
dev = load_dataset("cais/mmlu", subject, split="dev", revision=REVISION)
```

### 3. Score each answer letter

This builds the prompt exactly as `gen_prompt` and `format_example` do, including the header's double space before the subject name. The authors read the log-probabilities of ` A` to ` D`, each with a leading space, from the OpenAI API; their [Flan-T5 script](https://github.com/hendrycks/test/blob/4450500f923c49f1fb1dd3d99108a0bd9717b660/evaluate_flan.py) compares the logits of the letters instead.

```python
LETTERS = "ABCD"

def format_example(item, include_answer=True):
    text = item["question"] + "".join(f"\n{letter}. {choice}" for letter, choice in zip(LETTERS, item["choices"]))
    text += "\nAnswer:"
    if include_answer:
        text += f" {LETTERS[item['answer']]}\n\n"
    return text

subject_name = "".join(" " + word for word in subject.split("_"))
prompt = f"The following are multiple choice questions (with answers) about {subject_name}.\n\n"
prompt += "".join(format_example(example) for example in dev) + format_example(row, include_answer=False)

def score_choice(prompt: str, token: str) -> float:
    raise NotImplementedError("Call your model and return the log-probability that this token comes next.")

scores = [score_choice(prompt, f" {letter}") for letter in LETTERS]
prediction = LETTERS[scores.index(max(scores))]
```

### 4. Score it

The prediction is correct when it equals the reference letter. cais/mmlu stores the reference as an index from 0 to 3.

```python
print(prediction == LETTERS[row["answer"]])
```

### Score the full benchmark

`evaluate.py` repeats this for all 57 subjects from the authors' [data files](https://people.eecs.berkeley.edu/~hendrycks/data.tar), dropping examples only when a prompt exceeds 2,048 tokens. It prints accuracy for each subject and an overall `Average accuracy` over all 14,042 questions, so each subject counts in proportion to its size. It calls OpenAI's original GPT-3 engines, which are no longer served, so replace its `openai.Completion.create` call to use another model. [lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness/tree/v0.4.13/lm_eval/tasks/mmlu/default) v0.4.13's `mmlu` task loads the same questions and dev examples and scores the letters the same way, with a single space in the header and surrounding whitespace stripped from each question. It also weights subjects by size; ask it for the authors' five examples.

```sh
pip install "lm-eval[hf]==0.4.13"
lm-eval run --model hf --model_args pretrained=YOUR_MODEL --tasks mmlu --num_fewshot 5
```
