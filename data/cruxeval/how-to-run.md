The authors' [cruxeval](https://github.com/facebookresearch/cruxeval/tree/190faf16d175b5847b0af05d937872b1fb395942) repository has the prompt templates, the answer extraction and the scorer, which executes each predicted assertion and reports pass@1 and pass@5. Each sample poses two tasks: output prediction (CRUXEval-O) and input prediction (CRUXEval-I). Scoring runs model-written code, so run it inside a sandbox such as a Linux container; the scorer's worker processes assume Linux process forking.

### 1. Install the scorer

Scoring needs only the base requirements. The authors tested with Python 3.9.

```sh
git clone https://github.com/facebookresearch/cruxeval
git -C cruxeval checkout 190faf16d175b5847b0af05d937872b1fb395942
pip install -r cruxeval/requirements-base.txt
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream sample number padded to three digits. Save the Python steps as a script in the `cruxeval` directory and run it from there.

```python
import json
import sys

sys.path.append("evaluation")  # the scorer's modules import each other by name
from prompts import make_direct_input_prompt, make_direct_output_prompt
from utils_general import evaluate_score

key = "{{key}}"
sample_id = f"sample_{int(key.removeprefix('sample-'))}"
with open("data/cruxeval.jsonl", encoding="utf-8") as f:
    sample = next(s for s in map(json.loads, f) if s["id"] == sample_id)
```

### 3. Generate predictions

The direct prompts show two solved examples, then this sample's function and its assertion with `??` in place of the output or the input. The model completes the assertion and stops at `[/ANSWER]`. The extraction below is what the authors' inference tasks apply to direct-prompt generations: the text after `==` for output prediction, the call to `f` before it for input prediction.

```python
def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model, stop at [/ANSWER], and return its continuation of the prompt.")

def extract_output(reply):
    return reply.split("==")[1].strip() if "==" in reply else reply.strip()

def extract_input(reply):
    answer = reply.split("==")[0].strip() if "==" in reply else reply
    if "assert f" in answer:
        answer = "f" + answer.split("assert f")[1].strip()
    return answer.strip()

predicted_output = extract_output(generate(make_direct_output_prompt((sample["code"], sample["input"]))))
predicted_input = extract_input(generate(make_direct_input_prompt((sample["code"], sample["output"]))))
```

### 4. Score it

`evaluate_score` runs the function and asserts that the reference output equals the prediction, with a 3-second limit. A predicted output that just repeats the call is not run and counts as wrong. Any input that produces the reference output passes.

```python
reference = (sample["code"], sample["input"], sample["output"])
print("CRUXEval-O:", evaluate_score(([predicted_output], reference, "output"))[0])
print("CRUXEval-I:", evaluate_score(([predicted_input], reference, "input"))[0])
```

### Score the full benchmark

For each task, write a JSON object mapping every ID from `sample_0` to `sample_799` to a list of extracted predictions, then run the scorer from `cruxeval/evaluation`. It picks the mode from the file name, input when the path contains `input` and output otherwise, so name the files accordingly. It reports pass@1 and pass@5 as percentages averaged over the 800 samples.

```sh
python evaluate_generations.py --generations_path generations_input.json --scored_results_path scored_input.json --mode input
python evaluate_generations.py --generations_path generations_output.json --scored_results_path scored_output.json --mode output
```

### Verify with the Benchopedia sweep

Start Docker, run `python3 runner/python_sandbox.py`, and run
`python3 runner/sweep.py cruxeval --verify-grader`. Each sample gets two calls,
one for the output and one for the input. The grader records pass@1 separately
for each mode and runs each assertion in its own network-isolated container
with a three-second deadline. Use the full procedure above for pass@5.
