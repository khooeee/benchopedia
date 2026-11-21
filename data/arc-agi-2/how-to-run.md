ARC Prize's [arc-agi-benchmarking](https://github.com/arcprize/arc-agi-benchmarking/tree/a4e7c997a2015a3209d4bc7c778aab18faef1cdb) harness turns each test input of this task into a prompt, parses a grid from the model's response, and scores it by exact match with two attempts per test input. The task itself comes from the [ARC-AGI-2](https://github.com/arcprize/ARC-AGI-2/tree/f3283f727488ad98fe575ea6a5ac981e4a188e49) repository. Scoring only compares grids and runs no model-generated code.

### 1. Install the harness and fetch the tasks

The harness needs Python 3.10 or later.

```sh
git clone https://github.com/arcprize/ARC-AGI-2
git -C ARC-AGI-2 checkout f3283f727488ad98fe575ea6a5ac981e4a188e49
git clone https://github.com/arcprize/arc-agi-benchmarking
git -C arc-agi-benchmarking checkout a4e7c997a2015a3209d4bc7c778aab18faef1cdb
pip install -e arc-agi-benchmarking
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream task ID, the name of its JSON file.

```python
from arc_agi_benchmarking.schemas import ARCTask

key = "{{key}}"
task = ARCTask.load_from_file(f"ARC-AGI-2/data/evaluation/{key}.json")
```

### 3. Generate two attempts per test input

The harness builds one prompt per test input from its template: every demonstration pair and then the test input, each grid written as a JSON list of rows. The model is asked to respond in the format of the demonstration outputs. The harness makes two attempts for each test input by default.

```python
from arc_agi_benchmarking.prompts.prompt_manager import convert_task_pairs_to_prompt

def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return its response to the prompt.")

responses = [[generate(convert_task_pairs_to_prompt(task.train, pair)) for _ in range(2)]
             for pair in task.test]
```

### 4. Score it

`parse_and_validate_json` is the parser the harness applies to each response: it takes a grid inside `\boxed{...}`, or else the JSON that ends at the response's last closing bracket, if that is a list of lists. A test input is solved if either attempt equals its output grid exactly, and the task scores the share of its test inputs solved, as `ARCScorer.score_task` computes. The harness allows two calls per prediction slot when the first reply cannot be parsed. Benchopedia uses the same retry limit and keeps every returned reply in the run record. An empty slot after both calls counts as a miss. The short example below treats an unparseable reply as a miss without retrying.

```python
from arc_agi_benchmarking.utils.parsing import parse_and_validate_json

def parse(response):
    try:
        return parse_and_validate_json(response)
    except ValueError:
        return None

solved = [any(parse(response) == pair.output for response in attempts)
          for pair, attempts in zip(task.test, responses)]
print(sum(solved) / len(task.test))  # 1.0 when every test input is solved
```

### Score the full benchmark

Add a config for your model to `src/arc_agi_benchmarking/models.yml`, or pick an existing one, and set its API key. `run_all.py` runs every task in the folder with two attempts per test input, and the scorer sums the task scores and divides by the number of tasks, printing the result as a percentage.

```sh
cd arc-agi-benchmarking
CONFIG=random-baseline  # replace with your model's config name
python cli/run_all.py --config "$CONFIG" --data_dir ../ARC-AGI-2/data/evaluation \
  --save_submission_dir "submissions/$CONFIG"
python src/arc_agi_benchmarking/scoring/scoring.py --task_dir ../ARC-AGI-2/data/evaluation \
  --submission_dir "submissions/$CONFIG" --results_dir "results/$CONFIG"
```
