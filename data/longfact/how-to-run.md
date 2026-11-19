The authors' [long-form-factuality](https://github.com/google-deepmind/long-form-factuality/tree/9d27158d198ced0a9d8271a80147cae580614601) repository rates a response with SAFE, which splits it into facts and checks each one with a rater model and Google Search through the Serper API. `metric_utils.calculate_metrics` turns the counts into F1@K. Rating needs an OpenAI or Anthropic key for the rater and a Serper key.

### 1. Install the evaluator

The authors suggest Python 3.10. The pinned requirements include Linux CUDA packages and the spaCy model SAFE loads.

```sh
git clone https://github.com/google-deepmind/long-form-factuality
git -C long-form-factuality checkout 9d27158d198ced0a9d8271a80147cae580614601
pip install -r long-form-factuality/requirements.txt
```

### 2. Load this task

Benchopedia's key `{{key}}` is the task, the topic from the upstream file name in lowercase, and the prompt's two-digit line number in that file. The keys must be set before SAFE is imported, because it reads the Serper key at import time.

```python
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, "long-form-factuality")
from common import shared_config, utils

shared_config.openai_api_key = os.environ["OPENAI_API_KEY"]
shared_config.serper_api_key = os.environ["SERPER_API_KEY"]
from common import modeling
from eval import metric_utils
from eval.safe import config as safe_config
from eval.safe import search_augmented_factuality_eval as safe

key = "{{key}}"
task, rest = key.split("-", 1)
topic, line = rest.rsplit("-", 1)
folder = next(Path("long-form-factuality/longfact").glob(f"longfact-{task}_*_noduplicates"))
path = next(p for p in folder.glob("*.jsonl") if p.stem.lower() == f"longfact-{task}_{topic}")
prompt = json.loads(path.read_text(encoding="utf-8").split("\n")[int(line) - 1])["prompt"]
```

### 3. Generate a response

The authors' pipeline appends `prompt_postamble`, a request for specific names, numbers, dates and places, after a space. The paper decodes up to 1,024 tokens at temperature 0.

```python
full_prompt = utils.strip_string(f"{prompt} {utils.strip_string(shared_config.prompt_postamble)}")

def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return its long-form response.")

response = generate(full_prompt)
```

### 4. Score it

`safe.main` runs SAFE with the configured rater, by default GPT-3.5-Turbo with five search steps and three results per query. F1@K combines precision over supported and unsupported facts with recall against K facts; the paper reports K = 64 and K = 178.

```python
rater = modeling.Model(safe_config.model, temperature=safe_config.model_temp, max_tokens=safe_config.max_tokens)
result = safe.main(prompt=full_prompt, response=response, rater=rater)
supported, not_supported = result[safe.SUPPORTED_LABEL], result[safe.NOT_SUPPORTED_LABEL]
print(supported, not_supported, result[safe.IRRELEVANT_LABEL])
for k in (64, 178):
    print(f"F1@{k}", metric_utils.calculate_metrics(supported, not_supported, max_claims=k))
```

### Score the full benchmark

To benchmark an OpenAI or Anthropic model, add the keys to `common/shared_config.py` and set the responder in `main/config.py`. Its defaults match the paper: 250 random LongFact-Objects prompts. Then rate the results file the pipeline writes. `run_eval` computes F1@K for every prompt and prints the average across prompts.

```sh
cd long-form-factuality
python -m main.pipeline
python -m eval.run_eval --result_path=path/to/results.json --max_claim=64
```
