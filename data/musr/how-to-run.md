The authors' [eval.py](https://github.com/Zayne-sprague/MuSR/blob/b1f4d4168a9cfc6760e8b74d728e4516023dfaa5/eval/eval.py) builds a chain-of-thought prompt with a domain hint, reads the choice number from the model's last `ANSWER:` line, and counts the question correct when it names the gold choice. Its scoring is written inline rather than as a function, so steps 3 and 4 repeat it in a few lines.

### 1. Fetch the data and evaluation script

```sh
git clone https://github.com/Zayne-sprague/MuSR
git -C MuSR checkout b1f4d4168a9cfc6760e8b74d728e4516023dfaa5
```

### 2. Load this task

Benchopedia's key `{{key}}` is the domain and the question's one-based position after listing every story's questions in file order.

```python
import ast
import json
import random
from pathlib import Path

key = "{{key}}"
domain, number = key.rsplit("-", 1)
stories = json.loads(Path(f"MuSR/datasets/{domain.replace('-', '_')}.json").read_text(encoding="utf-8"))
story, question = [(s, q) for s in stories for q in s["questions"]][int(number) - 1]
```

### 3. Generate an answer

This uses the script's default `cot+` prompt. It reads the domain's system prompt and hint from `eval.py` without running the script, which needs an older dependency stack.

```python
settings = {}
for node in ast.walk(ast.parse(Path("MuSR/eval/eval.py").read_text(encoding="utf-8"))):
    if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
        settings[node.targets[0].id] = {k.value: ast.literal_eval(v)
                                        for k, v in zip(node.value.keys, node.value.values) if k.value != "ex"}
d = settings[{"murder-mystery": "murder_mysteries", "object-placements": "object_placements",
              "team-allocation": "team_allocation"}[domain]]

choices = "\n".join(f"{i + 1} - {c}" for i, c in enumerate(question["choices"]))
ending = ('Explain your reasoning step by step before you answer. Finally, the last thing you generate '
          'should be "ANSWER: (your answer here, including the choice number)"')
if d.get("hint_before_question"):
    prompt = (f'{story["context"]}\n\n{d["hint"]}\n\n{question["question"]}\n\n'
              f"Pick one of the following choices:\n{choices}\n\nYou must pick one option. {ending}")
else:
    prompt = (f'{story["context"]}\n\n{question["question"]}\n\nPick one of the following choices:\n'
              f'{choices}\n\nYou must pick one option. {d["hint"]} {ending}')

def generate(system_prompt: str, prompt: str) -> str:
    raise NotImplementedError("Call your model and return its full response.")

output = generate(d["system_prompt"], prompt)
```

### 4. Score it

As in `eval.py`, the answer is the text after `answer:` on the last lowercased line that has some. When it contains no choice number, the script guesses one at random. The question is correct when the answer contains the gold choice number.

```python
lines = [x.split("answer:")[-1].strip() for x in output.lower().split("\n")
         if "answer:" in x and x.split("answer:")[-1].strip()]
answer = lines[-1] if lines else ""
options = [str(i + 1) for i in range(len(question["choices"]))]
if not any(option in answer for option in options):
    answer = random.choice(options)
print(answer, str(question["answer"] + 1) in answer)
```

### Score the full benchmark

`eval.py` runs every question in the three domains with GPT-4 and prints correct over total for each domain, the accuracy the paper reports. Before running it, install `requirements.txt` (the authors tested Python 3.8), set `models_to_test`, start Redis or comment out `cache.enable()`, and change the murder-mystery `file_name` to `murder_mystery.json`, the file in `datasets/`. Run it as a module from the repository root so that `src` and `eval` import correctly.

```sh
cd MuSR
OPENAI_API_KEY=... python -m eval.eval
```
