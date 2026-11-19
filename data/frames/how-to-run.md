The FRAMES authors publish no evaluation code. The [paper](https://arxiv.org/abs/2409.12941v3) grades each free-form response with a rater model, using the auto-rating prompt in its Figure 6, and reports the share of questions the rater judges correct. This guide reproduces that prompt, with Gemini-Pro-1.5-0514 as the paper's rater.

### 1. Fetch the data

```sh
curl -LO https://huggingface.co/datasets/google/frames-benchmark/resolve/58d9fb6330f3ab1316d1eca12e5e8ef23dcc22ef/test.tsv
```

### 2. Load this task

Benchopedia's key `{{key}}` is `question-` followed by the question's zero-based row index in the file.

```python
import csv

key = "{{key}}"
with open("test.tsv", newline="", encoding="utf-8") as f:
    row = list(csv.DictReader(f, delimiter="\t"))[int(key.removeprefix("question-"))]
```

### 3. Generate a response

In the paper's naive setting the model receives the question alone. Its other settings add BM25-retrieved Wikipedia articles, or the text of the gold articles in the `wikipedia_link_` columns, to the question.

```python
def generate(question: str) -> str:
    raise NotImplementedError("Call your model and return its response.")

response = generate(row["Prompt"])
```

### 4. Score it

The rater receives the paper's system message and prompt with the question, the response and the gold answer filled in. The paper does not say how it reads the decision; this reads the text after the last `Decision:`.

```python
RATER_PROMPT = """===Task===

I need your help in evaluating an answer provided by an LLM against a ground truth answer. Your task is to determine if the ground truth answer is present in the LLM’s response. Please analyze the provided data and make a decision.

===Instructions===
1. Carefully compare the "Predicted Answer" with the "Ground Truth Answer".
2. Consider the substance of the answers – look for equivalent information or correct answers. Do not focus on exact wording unless the exact wording is crucial to the meaning.
3. Your final decision should be based on whether the meaning and the vital facts of the "Ground Truth Answer" are present in the "Predicted Answer:"

===Input Data===
- Question: <<question>>
- Predicted Answer: <<LLM_response>>
- Ground Truth Answer: <<ground_truth_answer>>

===Output Format===
Provide your final evaluation in the following format:
"Explanation:" (How you made the decision?)
"Decision:" ("TRUE" or "FALSE" )

Please proceed with the evaluation."""

def rate(system: str, user: str) -> str:
    raise NotImplementedError("Send these messages to the rater model and return its reply.")

reply = rate("You are a helpful assistant.", RATER_PROMPT
             .replace("<<question>>", row["Prompt"])
             .replace("<<LLM_response>>", response)
             .replace("<<ground_truth_answer>>", row["Answer"]))
print("TRUE" in reply.rsplit("Decision:", 1)[-1].upper())  # True when judged correct
```

### Score the full benchmark

There is no official runner. Repeat steps 2 to 4 for all 824 rows and report accuracy, the share of questions the rater judges TRUE. State the setting, any retrieval corpus, and the rater model, because the paper's results differ widely between settings.
