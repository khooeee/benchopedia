The authors' [simple-evals](https://github.com/openai/simple-evals/blob/652c89d0ca9df547706735883097e9537d40dc47/simpleqa_eval.py) harness asks the model each question and has a grader model compare the response with the reference answer. The grader uses the harness's `GRADER_TEMPLATE` and grades each response correct, incorrect or not attempted.

### 1. Install the harness

simple-evals needs Python 3.10 or later. Its SimpleQA module imports the packages below. The test file is published without versions, so it is checked against the digest Benchopedia imported.

```sh
git clone https://github.com/openai/simple-evals
git -C simple-evals checkout 652c89d0ca9df547706735883097e9537d40dc47
pip install pandas jinja2 numpy requests tqdm
curl -LO https://openaipublic.blob.core.windows.net/simple-evals/simple_qa_test_set.csv
echo "feee3f7e7db3617e94e8fcf1977b756ec420ef8568f4e0fcbbe0e92e9d5fc032  simple_qa_test_set.csv" | shasum -a 256 -c
```

### 2. Load this task

Benchopedia's key `{{key}}` is `test-` followed by the question's one-based row number in the file.

```python
import csv

key = "{{key}}"
with open("simple_qa_test_set.csv", newline="", encoding="utf-8") as f:
    row = list(csv.DictReader(f))[int(key.removeprefix("test-")) - 1]
```

### 3. Generate a response

The harness sends the question as the only user message, with no instructions added.

```python
def generate(question: str) -> str:
    raise NotImplementedError("Call your model and return its response.")

response = generate(row["problem"])
```

### 4. Score it

Run this from the folder that holds the clone. Its folder name contains a hyphen, so the module is loaded with `import_module`. The grader's reply is parsed as `grade_sample` does: the first A, B or C it contains, or C if there is none. The pinned harness grades with `gpt-4.1-2025-04-14` and the system message "You are a helpful assistant."

```python
import re
from importlib import import_module

simpleqa = import_module("simple-evals.simpleqa_eval")

def grade(prompt: str) -> str:
    raise NotImplementedError("Send this prompt to the grader model and return its reply.")

reply = grade(simpleqa.GRADER_TEMPLATE.format(
    question=row["problem"], target=row["answer"], predicted_answer=response))
match = re.search(r"(A|B|C)", reply)
print(simpleqa.CHOICE_LETTER_TO_STRING[match.group(0) if match else "C"])
```

### Score the full benchmark

Add a sampler for your model to the `models` dictionary in `simple_evals.py`, set `OPENAI_API_KEY` for the grader, and run the harness from the folder that holds the clone. `simple_evals.py` imports every eval and sampler, so it also needs `openai`, `anthropic`, `scipy`, `blobfile`, `tabulate` and the human-eval package. Over all 4,326 questions it reports the share correct, incorrect and not attempted, correct given attempted, and the F1 score, which is the harmonic mean of overall correct and correct given attempted.

```sh
python -m simple-evals.simple_evals --eval=simpleqa --model=<model_name>
```

### Verify with the Benchopedia sweep

Set `OPENAI_API_KEY` in the process environment for the dated judge. The
sweep sends the question to its OpenRouter model and checkpoints that answer
before calling the OpenAI judge. It records the judge call and the three
outcome indicators. Average the indicators over all questions and compute
accuracy given attempted and F1 from those aggregate rates.
