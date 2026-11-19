The authors publish the problems and translated few-shot examples in [url-nlp/mgsm](https://github.com/google-research/url-nlp/tree/452a21ad3dae5668c06ceeac21ff073e1e40f9be/mgsm) but no scoring code. This guide uses the paper's native chain-of-thought setting: six solved examples in the question's language, greedy decoding, and a step-by-step answer in that language. It implements the paper's rule that the final answer must equal the reference number.

### 1. Fetch the data

```sh
git clone https://github.com/google-research/url-nlp
git -C url-nlp checkout 452a21ad3dae5668c06ceeac21ff073e1e40f9be
```

### 2. Load this task

Benchopedia's key `{{key}}` is the language code and the problem's one-based line in that language's TSV file. Each line holds a question and its answer separated by a tab.

```python
import re
import sys
from pathlib import Path

sys.path.insert(0, "url-nlp/mgsm")
from exemplars import MGSM_EXEMPLARS

key = "{{key}}"
language, number = key.split("-")
lines = Path(f"url-nlp/mgsm/mgsm_{language}.tsv").read_text(encoding="utf-8").split("\n")
question, answer = lines[int(number) - 1].split("\t")
```

### 3. Generate an answer

The prompt is the first six of the authors' examples for this language, each a question and a step-by-step answer, separated by blank lines. The question of interest follows with the same localized labels, such as `Frage:` and `Schritt-für-Schritt-Antwort:` in German.

```python
def label(text: str) -> str:  # the localized "Question:" or "Step-by-Step Answer:" prefix
    return re.match(r"[^:：]*[:：] ?", text).group(0)

shots = [MGSM_EXEMPLARS[language][str(i)] for i in range(1, 7)]
prompt = "".join(f"{shot['q']}\n{shot['a']}\n\n" for shot in shots)
prompt += f"{label(shots[0]['q'])}{question}\n{label(shots[0]['a']).strip()}"

def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model with greedy decoding and return its step-by-step answer.")

response = generate(prompt).split(label(shots[0]["q"]).strip())[0]  # drop any next question
```

### 4. Score it

The examples end with the localized form of "The answer is 11.", so this takes the last number in the response, removes thousands separators, and compares it with the reference.

```python
numbers = re.findall(r"-?\d+(?:,\d{3})*(?:\.\d+)?", response)
prediction = float(numbers[-1].replace(",", "")) if numbers else None
print(prediction, answer, prediction == float(answer.replace(",", "")))
```

### Score the full benchmark

Run all 250 problems in each language and report each language's accuracy, the fraction answered correctly. The paper's average is the unweighted mean of the eleven language accuracies, English included; it also compares answering directly, reasoning in English, and translating the question to English first.
