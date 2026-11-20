The authors' [causalNLP/cladder](https://github.com/causalNLP/cladder/tree/3d2d1169b4b939a09048a6a75956c8972a93cc38) repository holds the questions in `data/cladder-v1.zip` and the evaluation script for this set in `causalbenchmark/eval/run_gpt_v1.5.py`. The script reads the data from a hard-coded folder outside the repository, imports the authors' `efficiency` package, and calls the OpenAI API. The steps below reproduce its prompt and answer rule with Python's standard library.

### 1. Load this task

Benchopedia's key `{{key}}` is the question's `question_id` in `cladder-v1-q-balanced.json`. The question's `model_id` points at the causal model in `cladder-v1-meta-models.json` whose `background` states the causal graph.

```python
import io
import json
import urllib.request
import zipfile

URL = "https://raw.githubusercontent.com/causalNLP/cladder/3d2d1169b4b939a09048a6a75956c8972a93cc38/data/cladder-v1.zip"
with urllib.request.urlopen(URL) as response:
    archive = zipfile.ZipFile(io.BytesIO(response.read()))
questions = json.loads(archive.read("cladder-v1-q-balanced.json"))
models = {model["model_id"]: model for model in json.loads(archive.read("cladder-v1-meta-models.json"))}

key = "{{key}}"
question = next(q for q in questions if str(q["question_id"]) == key)
```

### 2. Generate a solution

The script joins the model's background, the question's given information, and the question with single spaces, then adds a blank line and an instruction to start the answer with yes or no. With version 2.0 of the `efficiency` package, which formats the list of options, the instruction reads as below.

```python
INSTRUCTION = 'Start your answer with "Yes" or "No", followed by additional reasoning or evidence to support your explanation.'

def build_prompt(q):
    background = models[q["meta"]["model_id"]]["background"]
    return f'{background.strip()} {q["given_info"].strip()} {q["question"].strip()}\n\n{INSTRUCTION}'

def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return a reply that starts with Yes or No.")

completion = generate(build_prompt(question))
```

### 3. Score it

The script lowercases the reply, strips surrounding whitespace and double quotes, and reads yes or no from its start. A reply that starts with neither counts as wrong.

```python
def read_answer(completion):
    text = completion.lower().strip().strip('"')
    for answer in ("yes", "no"):
        if text.startswith(answer):
            return answer
    return None

print(read_answer(completion), read_answer(completion) == question["answer"])
```

### Score the full benchmark

Generate one reply for each of the 10,112 questions; accuracy is the fraction answered correctly. Half of the answers are yes, so guessing scores about 50%. The paper also reports accuracy by rung, which each question records in `q["meta"]["rung"]`.

```python
correct = [read_answer(generate(build_prompt(q))) == q["answer"] for q in questions]
print(sum(correct) / len(questions))
```
