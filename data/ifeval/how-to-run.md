The authors' [instruction_following_eval](https://github.com/google-research/google-research/tree/e6890f85757dd84e27ca6df2dd30651dafad28e0/instruction_following_eval) package loads this task, checks a response against each of its listed instructions, and reports strict and loose accuracy. It only inspects response text and runs no model-generated code.

### 1. Install the evaluator

The evaluator lives inside the large google-research repository, so fetch only its folder. Its requirements.txt names `absl`, which is published as `absl-py`. The scorer loads NLTK's Punkt sentence tokenizer by its old pickle name; NLTK 3.10.4 maps that name to the `punkt_tab` data.

```sh
git clone --filter=blob:none --sparse https://github.com/google-research/google-research
git -C google-research sparse-checkout set instruction_following_eval
git -C google-research checkout e6890f85757dd84e27ca6df2dd30651dafad28e0
pip install absl-py langdetect immutabledict "nltk==3.10.4"
python3 -m nltk.downloader punkt_tab
export PYTHONPATH="$PWD/google-research"
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream record's integer `key`.

```python
from instruction_following_eval import evaluation_lib

key = "{{key}}"
inputs = evaluation_lib.read_prompt_list(
    "google-research/instruction_following_eval/data/input_data.jsonl")
inp = next(example for example in inputs if example.key == int(key))
```

### 3. Generate a response

The model receives the prompt exactly as published, as a single user turn, and returns its full response. The instruction IDs and their parameters are for grading only.

```python
def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return its response to the prompt.")

response = generate(inp.prompt)
```

### 4. Score it

The strict check tests the response as written. The loose check also accepts an instruction if it passes after removing asterisks, the first line, the last line, or both lines. Empty responses fail.

```python
prompt_to_response = {inp.prompt: response}
for name, test in [("strict", evaluation_lib.test_instruction_following_strict),
                   ("loose", evaluation_lib.test_instruction_following_loose)]:
    result = test(inp, prompt_to_response)
    print(name, result.follow_all_instructions,
          dict(zip(result.instruction_id_list, result.follow_instruction_list)))
```

### Score the full benchmark

Write one JSON line per prompt, `{"prompt": ..., "response": ...}`, covering all 541 tasks, then run the authors' scorer from the google-research directory. For both strict and loose checks it reports prompt-level accuracy, the fraction of prompts whose instructions all pass, and instruction-level accuracy, the fraction of all listed instructions that pass.

```sh
cd google-research
mkdir -p results
python3 -m instruction_following_eval.evaluation_main \
  --input_data=./instruction_following_eval/data/input_data.jsonl \
  --input_response_data=../responses.jsonl \
  --output_dir=./results
```
