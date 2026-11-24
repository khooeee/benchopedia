Facebook's [MemN2N answer parser](https://github.com/facebookarchive/MemNN/blob/d7c5f6d5e1a4af6417ffff98535a96bb0947a6a8/MemN2N-babi-matlab/parseBabiTask.m) lowercases the complete answer label, and its [test script](https://github.com/facebookarchive/MemNN/blob/d7c5f6d5e1a4af6417ffff98535a96bb0947a6a8/MemN2N-babi-matlab/test.m) measures classification error against that label. These steps use the same comparison with a text-generating model and the v1.2 English test data documented in [Henaff et al., section 5.2](https://arxiv.org/abs/1612.03969v1).

### 1. Download the archive

Fetch the [Facebook archive pinned by ParlAI](https://github.com/facebookresearch/ParlAI/blob/a29567f7ce76992fd1f03c51ba9e3b155a37ea51/parlai/tasks/babi/build.py). The code below needs Python 3.9 or later.

```sh
curl -fL https://dl.fbaipublicfiles.com/parlai/babi/babi.tar.gz -o babi.tar.gz
```

### 2. Load this task

The key `{{key}}` gives the category and the one-based question number within its `en-10k` test file.

```python
from hashlib import sha256
from io import BytesIO
from pathlib import Path
import tarfile

key = "{{key}}"
category, number = map(int, key.removeprefix("qa").split("-"))
payload = Path("babi.tar.gz").read_bytes()
assert sha256(payload).hexdigest() == "f7f0bee187efca0d81c3daac1b162cda4eb7f9505dee5ad6846eabbed3dbf92e"

def questions(archive, category):
    prefix = f"tasks_1-20_v1-2/en-10k/qa{category}_"
    name, = (name for name in archive.getnames()
             if name.startswith(prefix) and name.endswith("_test.txt"))
    statements = []
    with archive.extractfile(name) as stream:
        for raw in stream:
            line, text = raw.decode("utf-8").rstrip("\r\n").split(" ", 1)
            if line == "1":
                statements.clear()
            if "\t" in text:
                question, answer, _ = text.split("\t")
                context = "\n".join(statements)
                yield f"{context}\n\nQuestion: {question}", answer
            else:
                statements.append(text)

with tarfile.open(fileobj=BytesIO(payload), mode="r:gz") as archive:
    prompt, reference = list(questions(archive, category))[number - 1]
```

### 3. Generate an answer

Send the preceding story statements and the selected question. Supporting-fact IDs and reference answers are held out during prediction.

```python
def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return its answer text.")

instruction = "Reply with just the answer label. Separate multiple answer parts with commas."
prediction = generate(f"{prompt}\n\n{instruction}")
```

### 4. Score it

Compare the complete label after lowercasing and trimming spaces around each comma-separated part. The chat adapter accepts a final period and a leading `the` before a part. The order of parts remains significant, including directions in a path-finding answer.

```python
import re

def correct(prediction, reference):
    response = prediction.strip().lower().removesuffix(".")
    label = ",".join(part.strip().removeprefix("the ") for part in response.split(","))
    if not re.fullmatch(r"[a-z0-9'-]+(?:\s*,\s*[a-z0-9'-]+)*", label):
        return False
    return label == reference.lower()

print(correct(prediction, reference))
```

### Score the full benchmark

Score all 1,000 questions in each category. The [original paper](https://arxiv.org/abs/1502.05698v10) reports category accuracy, mean accuracy, and the number of categories below 95% accuracy.

```python
with tarfile.open(fileobj=BytesIO(payload), mode="r:gz") as archive:
    accuracy = {}
    for category in range(1, 21):
        rows = list(questions(archive, category))
        assert len(rows) == 1000
        hits = sum(correct(generate(f"{prompt}\n\n{instruction}"), reference)
                   for prompt, reference in rows)
        accuracy[category] = hits / len(rows)

for category, score in accuracy.items():
    print(f"qa{category:02d}: {score:.1%}")
print("Mean accuracy", sum(accuracy.values()) / len(accuracy))
print("Categories below 95%", sum(score < 0.95 for score in accuracy.values()))
```
