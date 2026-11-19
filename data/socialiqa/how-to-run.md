SocialIQA's authors publish no scoring script. Their [paper](https://arxiv.org/abs/1904.09728) reports accuracy: the fraction of questions where the chosen answer, A, B or C, is the reference answer. This guide implements that rule on the version 1.4 test file this snapshot was imported from.

### 1. Download the data

Check that the archive is the version this snapshot was imported from.

```sh
curl -LO https://maartensap.com/social-iqa/data/socialIQa_v1.4.tgz
echo "99a399d50f1a996388e94ab435ba0ceadc6b8ad9d90e6420358c962a4850d217  socialIQa_v1.4.tgz" | shasum -a 256 -c
mkdir socialiqa && tar -xzf socialIQa_v1.4.tgz -C socialiqa
```

### 2. Load this task

The file has no question IDs. Benchopedia's key `{{key}}` is the question's one-based line number in `socialIQa_v1.4_tst.jsonl`.

```python
import json

key = "{{key}}"
with open("socialiqa/socialIQa_v1.4_tst.jsonl", encoding="utf-8") as f:
    row = json.loads(f.readlines()[int(key.removeprefix("socialiqa-")) - 1])
```

### 3. Generate an answer

The authors publish no prompt for language models; their baselines are fine-tuned classifiers. This sends the context, the question and the lettered answers as this page shows them. Add an instruction if your model needs one.

```python
def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return the letter of the best answer, A, B or C.")

answers = "\n".join(f"{letter}. {row['answer' + letter]}" for letter in "ABC")
prediction = generate(f"{row['context']}\n\n{row['question']}\n\n{answers}").strip()
```

### 4. Score it

The row's `correct` field holds the reference letter.

```python
print(prediction == row["correct"])
```

### Score the full benchmark

Repeat steps 2 to 4 for all 2,224 lines of the test file and report the fraction answered correctly. lm-evaluation-harness's `social_iqa` task scores the development split instead, so its results do not measure this test set.
