OpenAI's reference implementation, [healthbench_eval.py](https://github.com/openai/simple-evals/blob/652c89d0ca9df547706735883097e9537d40dc47/healthbench_eval.py) in simple-evals, has a grader model judge a response against each physician-written rubric criterion for its conversation and turns the criteria met into a score. Both the model under test and the grader are called through an API, by default OpenAI's.

### 1. Install the harness

The repository is not a package, so clone it under a name Python can import, next to your script.

```sh
git clone https://github.com/openai/simple-evals simple_evals
git -C simple_evals checkout 652c89d0ca9df547706735883097e9537d40dc47
pip install openai blobfile numpy pandas jinja2 requests tqdm
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream `prompt_id`, and the file below is the one the harness reads.

```python
import json
import urllib.request

key = "{{key}}"
url = "https://openaipublic.blob.core.windows.net/simple-evals/healthbench/2025-05-07-06-14-12_oss_eval.jsonl"
with urllib.request.urlopen(url) as f:
    example = next(e for e in map(json.loads, f) if e["prompt_id"] == key)
```

### 3. Generate a response

The model receives the conversation as a list of `{"role": ..., "content": ...}` messages ending with a user message, and returns the next assistant message. The harness's OpenAI samplers prepend the system message "You are a helpful assistant."; put any system message you send into `messages`, because the grader sees it too.

```python
def generate(messages: list[dict]) -> str:
    raise NotImplementedError("Call your model and return its reply to the conversation.")

messages = example["prompt"]
response = generate(messages)
```

### 4. Score it

For each rubric criterion, the harness fills its grader template with the conversation and the criterion, asks the grader for JSON with a boolean `criteria_met`, and asks again until it gets one. Its default grader is `gpt-4.1-2025-04-14` with the system message "You are a helpful assistant.". `calculate_score` adds the points of the criteria met, including negative ones, and divides by the total of the positive points.

```python
from simple_evals.healthbench_eval import GRADER_TEMPLATE, RubricItem, calculate_score, parse_json_to_dict

def grade(grader_prompt: str) -> str:
    raise NotImplementedError("Send grader_prompt to the grader model as a user message and return its reply.")

rubric = [RubricItem.from_dict(item) for item in example["rubrics"]]
turns = messages + [{"role": "assistant", "content": response}]
conversation = "\n\n".join(f"{m['role']}: {m['content']}" for m in turns)
verdicts = []
for item in rubric:
    grader_prompt = GRADER_TEMPLATE.replace("<<conversation>>", conversation).replace("<<rubric_item>>", str(item))
    verdict = {}
    while not isinstance(verdict.get("criteria_met"), bool):
        verdict = parse_json_to_dict(grade(grader_prompt))
    verdicts.append(verdict)
print(calculate_score(rubric, verdicts))  # below 0 when penalties outweigh credit
```

### Score the full benchmark

The harness's command runs a model from its built-in list on all 5,000 conversations with the default grader, with `OPENAI_API_KEY` set; to score another model, add a `SamplerBase` for it to the `models` dictionary in `simple_evals.py`. The command imports every eval in the repository, so it also needs `anthropic`, `scipy`, `tabulate` and [human-eval](https://github.com/openai/human-eval) installed.

```sh
python -m simple_evals.simple_evals --eval=healthbench --model=gpt-4.1
```

The HealthBench score is the mean of the per-conversation scores, with the mean clipped to the range 0 to 1 and reported with a bootstrap standard deviation. Scores for each theme and each rubric axis are averaged the same way.

### Verify with the Benchopedia sweep

Run `python3 data/healthbench/setup_eval.py` to fetch the checksum-pinned
rubrics into the local build directory. Set `OPENAI_API_KEY` in the process
environment for the dated judge. The sweep records the OpenRouter response
and the judge's reply for every criterion. It retries replies that lack a
boolean decision. The run records the raw scores so they can be averaged
before applying the benchmark's clipping and bootstrap procedure.
