The ProofWriter datasets come as one archive from AI2, [`proofwriter-dataset-V2020.12.3.zip`](https://aristo-data-public.s3.amazonaws.com/proofwriter/proofwriter-dataset-V2020.12.3.zip), with a README describing its fields, and no scoring script. The [paper](https://arxiv.org/abs/2012.13048) scores answer accuracy, the fraction of questions answered True, False, or Unknown correctly, and proof accuracy, where a generated proof must exactly match one of the gold proofs. The steps below score the answer with Python's standard library.

### 1. Load this task

Benchopedia's key `{{key}}` joins a theory's `id` in `OWA/depth-5/meta-test.jsonl` with the question's name in that theory's `questions`, such as `Q1`.

```python
import hashlib
import io
import json
import urllib.request
import zipfile

URL = "https://aristo-data-public.s3.amazonaws.com/proofwriter/proofwriter-dataset-V2020.12.3.zip"
with urllib.request.urlopen(URL) as response:
    data = response.read()
assert hashlib.sha256(data).hexdigest() == "bbc5694901e8306d0bd659aa1ad53ccfd02c201864f4b320ffa3777827d1fc26"
lines = zipfile.ZipFile(io.BytesIO(data)).read("proofwriter-dataset-V2020.12.3/OWA/depth-5/meta-test.jsonl").decode("utf-8").splitlines()
theories = {theory["id"]: theory for theory in map(json.loads, lines)}

key = "{{key}}"
theory_id, name = key.rsplit("-", 1)
theory = theories[theory_id]
question = theory["questions"][name]
```

### 2. Generate an answer

The dataset has no prompt. Benchopedia's gives the theory, the statement, and the open-world meaning of the three answers.

```python
LABELS = {True: "True", False: "False", "Unknown": "Unknown"}
INSTRUCTION = ("Using only the facts and rules above, is the statement true, false, or unknown? "
               "It is true if it follows from them, false if its negation follows from them, "
               "and unknown if neither does.")

def build_prompt(theory, question):
    return f"{theory['theory']}\n\nStatement: {question['question']}\n\n{INSTRUCTION}"

def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return its answer: True, False, or Unknown.")

completion = generate(build_prompt(theory, question))
```

### 3. Score it

The answer is correct when it names the label. True and false questions also carry every possible proof of the answer in `question["proofs"]`, separated by `OR`, for scoring generated proofs.

```python
def read_answer(completion):
    words = completion.strip().split()
    word = words[-1].strip(".*\"'").capitalize() if words else ""
    return word if word in LABELS.values() else None

print(read_answer(completion), read_answer(completion) == LABELS[question["answer"]])
```

### Score the full benchmark

Generate one answer for each of the 20,030 questions; answer accuracy is the fraction answered correctly. The paper also reports it by proof depth, which each true or false question records in `question["QDep"]`, with unknown questions as a separate group.

```python
questions = [(theory, question) for theory in theories.values() for question in theory["questions"].values()]
correct = [read_answer(generate(build_prompt(t, q))) == LABELS[q["answer"]] for t, q in questions]
print(sum(correct) / len(questions))
```
