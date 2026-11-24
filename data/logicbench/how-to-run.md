Follow the binary question-answering protocol in [Section 4.1 of the LogicBench paper](https://arxiv.org/html/2404.15522v2#S4.SS1) and the three zero-shot prompting designs in [Appendix H.2](https://arxiv.org/html/2404.15522v2#A8.SS2). The authors' repository provides the labeled data. This implementation uses the paper's scoring rules and its own wording for the prompts.

### Fetch the evaluation split

Use Python 3 from the Benchopedia repository root. The importer fetches all 25 binary question-answering files from the pinned release and verifies their checksums.

### Load this task

The key gives the source family, rule directory, sample ID, and one-based position of the question in that sample.

```python
import runpy

source = runpy.run_path("data/logicbench/import.py")
evaluation = runpy.run_path("data/logicbench/eval.py")
tasks = {task["key"]: task for task in source["load_tasks"]()}

key = "{{key}}"
task = tasks[key]
```

### Generate three labels

Each call uses the same original context and question with a different instruction. Start a fresh conversation for each call and use the same model configuration throughout.

```python
def generate(messages):
    raise NotImplementedError("Call your model here")

def replies_for(task):
    replies = []
    while True:
        messages = evaluation["next_messages"](task, replies)
        if messages is None:
            return replies
        replies.append(generate(messages))

replies = replies_for(task)
```

### Score the task

Read the final yes or no label and compare it with the source label. A missing or malformed label receives zero credit. The task score is the fraction of the three replies that match.

```python
print([evaluation["label"](reply) for reply in replies])
print(evaluation["score_responses"](task, replies))
```

### Score the full benchmark

Evaluate all 1,520 questions. The averages within each rule and reference label give A(Yes) and A(No). The mean of the rule scores within each family gives its two label scores as in the paper's Table 6.

```python
from collections import defaultdict
from statistics import mean

by_rule = defaultdict(list)
for task in tasks.values():
    family, rule, _, _ = task["key"].split(".")
    label = task["solution"]
    score = evaluation["score_responses"](task, replies_for(task))["accuracy"]
    by_rule[family, rule, label].append(score)

by_family = defaultdict(list)
for (family, rule, label), scores in sorted(by_rule.items()):
    accuracy = mean(scores)
    print(family, rule, label, accuracy)
    by_family[family, label].append(accuracy)

for (family, label), scores in sorted(by_family.items()):
    print(family, label, mean(scores))
```
