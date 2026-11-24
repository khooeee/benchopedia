Use direct, trace-level mistake localization from [Section 3 of the BIG-Bench Mistake paper](https://arxiv.org/html/2311.08516#S3.SS1) and the [pinned three-shot prompt modules](https://github.com/WHGTyen/BIG-Bench-Mistake/tree/9b010ce17150b79411dc31659779d7524c03f436/mistake_finding_prompts).

### Fetch the trace release

Use Python 3 from the Benchopedia repository root. The importer fetches the five trace files from the pinned Git revision and verifies their checksums. The accompanying prompt data contains the authors' direct templates and demonstrations.

### Load this task

The key identifies the original source file and its one-based JSONL row number. The importer numbers the steps as `Thought 1`, `Thought 2`, and so on. The first mistake annotation moves from zero-based indexing to the same one-based scale.

```python
import runpy

source = runpy.run_path("data/big-bench-mistake/import.py")
evaluation = runpy.run_path("data/big-bench-mistake/eval.py")
tasks = {task["key"]: task for task in source["load_tasks"]()}

key = "{{key}}"
task = tasks[key]
```

### Generate the mistake location

Send the authors' three demonstrations and the complete trace as a single conversation. The final reply gives the number of the first mistaken step or `No` when the model finds none.

```python
def generate(messages):
    raise NotImplementedError("Call your model here")

reply = generate(evaluation["messages"](task))
```

### Score the location

Match the final label to the published annotation. Use the annotation for the first mistake even when the trace happens to reach the right final answer. A malformed response receives zero credit.

```python
verdict, label = evaluation["grade"](task, reply)
print(label, int(verdict == "pass"))
```

### Score the full benchmark

Evaluate all 2,186 traces with a fixed model configuration. Report the fraction of exact matches for each task family and separately for traces that have a mistake and traces annotated as mistake-free. These scores use all 986 Dyck language traces in the release. [Paper Table 2](https://arxiv.org/html/2311.08516#S2.T2) [Paper Appendix E](https://arxiv.org/html/2311.08516#A5)

```python
from collections import defaultdict
from statistics import mean

scores = defaultdict(list)
for task in tasks.values():
    family = task["key"].rsplit("-", 1)[0]
    reply = generate(evaluation["messages"](task))
    verdict, _ = evaluation["grade"](task, reply)
    correct = int(verdict == "pass")
    category = "mistake-free" if task["solution"] == "No" else "mistake"
    scores[family, "all"].append(correct)
    scores[family, category].append(correct)

for (family, category), results in sorted(scores.items()):
    print(family, category, mean(results))
```
