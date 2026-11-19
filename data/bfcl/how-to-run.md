The authors' [bfcl_eval](https://github.com/ShishirPatil/gorilla/tree/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard) harness prompts the model with this entry, runs any multi-turn or agentic exchange against its simulated backends, and scores the result with the category's checker. The harness drives the conversation itself, so the model plugs in as a harness model rather than a single function call.

### 1. Install the harness

The authors use Python 3.10. Copy the example `.env` and fill in the API key for your model; web search entries also need a SerpAPI key.

```sh
git clone --filter=blob:none --sparse https://github.com/ShishirPatil/gorilla
git -C gorilla sparse-checkout set berkeley-function-call-leaderboard
git -C gorilla checkout 6ea57973c7a6097fd7c5915698c54c17c5b1b6c8
pip install -e gorilla/berkeley-function-call-leaderboard
cp gorilla/berkeley-function-call-leaderboard/bfcl_eval/.env.example \
  gorilla/berkeley-function-call-leaderboard/.env
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream entry ID, and the ID without its final `_` part is its category. The harness runs each web search question twice, with and without search snippets, and each memory question once per memory backend after the conversations of its scenario, under IDs that name the variant. The code lists those IDs in the file `bfcl generate --run-ids` reads.

```python
import json
from bfcl_eval.constants.category_mapping import MEMORY_CATEGORY, WEB_SEARCH_CATEGORY
from bfcl_eval.constants.eval_config import MEMORY_PREREQ_CONVERSATION_PATH, PROJECT_ROOT
from bfcl_eval.utils import load_dataset_entry, load_file

key = "{{key}}"
category = key.rsplit("_", 1)[0]
if category == "memory_prereq":
    raise SystemExit("Memory conversations are not scored; run a memory question from the same scenario.")
if category == "web_search":
    run_ids = {variant: [key.replace("web_search", variant)] for variant in WEB_SEARCH_CATEGORY}
elif category == "memory":
    scenario = key.split("-")[1]
    prereqs = [entry["id"] for entry in load_file(MEMORY_PREREQ_CONVERSATION_PATH / f"memory_{scenario}.json")]
    run_ids = {backend: [entry_id.replace("memory", backend) for entry_id in prereqs + [key]]
               for backend in MEMORY_CATEGORY}
else:
    run_ids = {category: [key]}
(PROJECT_ROOT / "test_case_ids_to_generate.json").write_text(json.dumps(run_ids, indent=2))
first = next(iter(run_ids))
entry = next(e for e in load_dataset_entry(first) if e["id"] == run_ids[first][-1])
print(entry["question"])  # the turns as the harness loads them
```

### 3. Generate the model's responses

Pick a model name from the harness's [SUPPORTED_MODELS.md](https://github.com/ShishirPatil/gorilla/blob/6ea57973c7a6097fd7c5915698c54c17c5b1b6c8/berkeley-function-call-leaderboard/SUPPORTED_MODELS.md), or add a handler for your own model as its CONTRIBUTING.md describes. The harness adds its system prompt and function documentation, and for multi-turn and agentic entries executes the model's calls and feeds back the results.

```python
import subprocess

model = "gpt-4o-2024-11-20-FC"  # replace with your model's name in the harness
subprocess.run(["bfcl", "generate", "--model", model, "--run-ids"], check=True)
```

### 4. Score it

`--partial-eval` scores only the entries that were generated. Each category's score file starts with a summary line whose accuracy is 1.0 if this entry passed and 0.0 if it failed; the failure details follow it.

```python
subprocess.run(["bfcl", "evaluate", "--model", model, "--test-category", ",".join(run_ids),
                "--partial-eval"], check=True)
for name in run_ids:
    score_dir = PROJECT_ROOT / "score" / model.replace("/", "_")
    with open(next(score_dir.rglob(f"BFCL_v4_{name}_score.json"))) as f:
        print(name, json.loads(f.readline())["accuracy"])
```

### Score the full benchmark

Generate and evaluate every scored category. Each category's accuracy is the share of its entries that pass; `score/data_overall.csv` combines them into the overall score, weighting agentic at 40%, multi-turn at 30%, and live, non-live, and hallucination measurement at 10% each.

```sh
cd gorilla/berkeley-function-call-leaderboard
bfcl generate --model gpt-4o-2024-11-20-FC --test-category all_scoring
bfcl evaluate --model gpt-4o-2024-11-20-FC --test-category all_scoring
```
