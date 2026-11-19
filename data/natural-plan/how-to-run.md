The authors' [natural-plan](https://github.com/google-deepmind/natural-plan/tree/ca76db336072ff8931db43bc1ca8d381038cf073) repository holds the test data and one evaluation script per task, which parse a model's plan and compare it with the golden plan. The scripts only parse text and run no model-generated code.

### 1. Fetch the data and evaluation scripts

```sh
git clone https://github.com/google-deepmind/natural-plan
git -C natural-plan checkout ca76db336072ff8931db43bc1ca8d381038cf073
pip install absl-py
```

### 2. Load this task

Benchopedia's key `{{key}}` is the task name with hyphens and the upstream example number padded to four digits. The task name also picks the data file and evaluation script.

```python
import json

key = "{{key}}"
name, number = key.rsplit("-", 1)
task = name.replace("-", "_")  # trip_planning, meeting_planning or calendar_scheduling
with open(f"natural-plan/data/{task}.json", encoding="utf-8") as f:
    example = json.load(f)[f"{task}_example_{int(number)}"]
```

### 3. Generate a plan

The authors run inference on the five-shot prompt, `prompt_5shot`, whose solved examples show the answer format the scripts parse. The model returns its plan in that format: the trip and calendar prompts end with `SOLUTION:`, and the meeting prompt asks for a response that starts with it.

```python
def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return its plan for the prompt.")

response = generate(example["prompt_5shot"])
```

### 4. Score it

This calls the per-example functions of the task's script, as its `main` does. Trip Planning needs the parsed cities and stay lengths to match the golden plan in order; Calendar Scheduling needs the first `Day, HH:MM - HH:MM` in the response to match; Meeting Planning replays the plan and needs it to meet as many friends as the golden plan does.

```python
import importlib
import sys

sys.path.insert(0, "natural-plan")
evaluate = importlib.import_module(f"evaluate_{task}")  # import one: all three define the same flag
if task == "trip_planning":
    plan = evaluate.parse_response(response)
    correct = evaluate.compute_example_score(example["cities"], example["durations"], plan) == 1.0
elif task == "calendar_scheduling":
    correct = evaluate.compute_solve_rate([response], [example["golden_plan"]]) == 1.0
else:
    start_location, initial_time = example["constraints"][0]
    constraints = evaluate.process_constraints(example["constraints"][1:])
    def friends_met(plan):
        return evaluate.validator_from_text(
            plan, constraints, start_location, initial_time, example["dist_matrix"])
    correct = friends_met(evaluate.parse_text_plan(response)) == friends_met(example["golden_plan"])
print(correct)
```

### Score the full benchmark

The scripts score the responses stored in each example's `pred_5shot_pro` field. Write a copy of each data file with your model's responses in that field, then run each script on its copy. Each reports the share of its examples solved; the meeting and calendar scripts also break it down by number of friends, or of attendees and days.

```sh
cd natural-plan
python3 evaluate_trip_planning.py --data_path=trip_planning_responses.json
python3 evaluate_meeting_planning.py --data_path=meeting_planning_responses.json
python3 evaluate_calendar_scheduling.py --data_path=calendar_scheduling_responses.json
```
