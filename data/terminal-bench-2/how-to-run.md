[Harbor](https://github.com/harbor-framework/harbor/tree/3cb627394b95d3ae605f31e0d694edf508cf4b7b), the official harness, builds this task's Docker container, lets an agent work in it until it stops or hits the time limit, then copies in the task's tests and records a reward of 1 if they all pass and 0 otherwise. The agent runs arbitrary commands, but only inside the task's container; Harbor uses local Docker by default, or a cloud sandbox with `--env`.

### 1. Install Harbor and fetch the tasks

Harbor 0.26.0 needs Python 3.12 or later and a running Docker daemon.

```sh
pip install "harbor==0.26.0"
git clone https://github.com/harbor-framework/terminal-bench-2
git -C terminal-bench-2 checkout f5b891cb4f7c20e306f9d05887628b43af740f43
```

### 2. Load this task

Benchopedia's key `{{key}}` is the task's directory name. The directory holds the instruction, `task.toml` with the time limits and container resources, the environment, the tests, and the reference solution.

```python
from pathlib import Path

key = "{{key}}"
task_dir = Path("terminal-bench-2") / key
print((task_dir / "instruction.md").read_text())
```

### 3. Run an agent on it

The agent receives the instruction and a terminal in the container. This uses the authors' Terminus 2 agent; Harbor also runs agents such as `claude-code`, or your own as `--agent module.path:ClassName`. Set the API key your model needs, such as `ANTHROPIC_API_KEY`. The `oracle` agent runs the reference solution instead, which checks that the environment works.

```python
import subprocess

job = f"tb2-{key}"
subprocess.run(["harbor", "run", "--path", str(task_dir), "--agent", "terminus-2",
                "--model", "anthropic/claude-opus-5-5", "--job-name", job])
```

### 4. Score it

Harbor scores the trial as soon as the agent finishes and writes each trial's `result.json` under `jobs/`. The verifier's reward is 1 if every test passed and 0 otherwise.

```python
import json

for result_file in Path("jobs", job).glob("*/result.json"):
    result = json.loads(result_file.read_text())
    print(result["trial_name"], (result["verifier_result"] or {}).get("rewards"))
```

### Score the full benchmark

Run all 89 tasks from Harbor's registry entry for the benchmark, which pins the same task files. The score is the resolution rate, the mean reward over tasks; the paper runs each agent and model pair at least five times, which `--n-attempts 5` does, and reports the mean with a 95% confidence interval.

```sh
harbor run --dataset terminal-bench@2.0 --agent terminus-2 \
  --model anthropic/claude-opus-5-5 --n-concurrent 4 --n-attempts 5
```
