BIRD's [evaluation script](https://github.com/AlibabaResearch/DAMO-ConvAI/blob/7635e3f7fd7136cddc462d7f184fd497d5bd5e4c/bird/llm/src/evaluation.py) runs the predicted and gold queries on the question's SQLite database and counts a match when they return the same set of rows; the share of matches is execution accuracy (EX). Predicted queries run directly against the database files and can change them, so score against a copy you can replace.

### 1. Fetch the databases and the scorer

Download the BIRD Dev package linked from the [dataset card](https://huggingface.co/datasets/birdsql/bird_sql_dev_20251106/blob/3c11fb193e5439b338e23677fa0aae11e8b85db9/README.md) and unpack it. The scorer expects a folder holding one `<db_id>/<db_id>.sqlite` per database; set `db_root` below to that folder. Save the Python steps as a script next to `evaluation.py`.

```sh
pip install datasets func_timeout
curl -LO https://raw.githubusercontent.com/AlibabaResearch/DAMO-ConvAI/7635e3f7fd7136cddc462d7f184fd497d5bd5e4c/bird/llm/src/evaluation.py
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream `question_id` padded to four digits.

```python
from datasets import load_dataset

db_root = "dev_databases"  # the unpacked folder of <db_id>/<db_id>.sqlite files
key = "{{key}}"
question_id = int(key.removeprefix("question-"))
dataset = load_dataset("birdsql/bird_sql_dev_20251106", split="dev_20251106",
                       revision="3c11fb193e5439b338e23677fa0aae11e8b85db9")
row = dataset[question_id]
assert row["question_id"] == question_id
db_path = f"{db_root}/{row['db_id']}/{row['db_id']}.sqlite"
```

### 3. Generate a query

BIRD's [baseline prompt](https://github.com/AlibabaResearch/DAMO-ConvAI/blob/7635e3f7fd7136cddc462d7f184fd497d5bd5e4c/bird/llm/src/gpt_request.py) gives each table's CREATE TABLE statement, the evidence as external knowledge and the question, and ends with `SELECT` for the model to continue. The baseline stops generation at `--`, a blank line, `;` or `#` and puts `SELECT` back in front of the continuation. Leaderboard results that use the evidence are marked as using oracle knowledge.

```python
import sqlite3

with sqlite3.connect(db_path) as conn:
    schema = "\n\n".join(sql for (sql,) in conn.execute("SELECT sql FROM sqlite_master WHERE type='table'"))
prompt = (schema + "\n\n"
          + f"-- External Knowledge: {row['evidence']}\n"
          + "-- Using valid SQLite and understading External Knowledge, answer the following questions for the tables provided above.\n"
          + f"-- {row['question']}"
          + "\nGenerate the SQL after thinking step by step: \nSELECT ")

def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model, stop at --, a blank line, ; or #, and return its continuation.")

predicted_sql = "SELECT" + generate(prompt)
```

### 4. Score it

`execute_model` runs both queries with the script's default 30-second limit. A query that fails or times out scores 0.

```python
from evaluation import execute_model

result = execute_model(predicted_sql, row["SQL"], db_path, question_id, 30.0)
print(result["res"])  # 1 if the two queries return the same set of rows, otherwise 0
```

### Score the full benchmark

The script reads two files from directories given with trailing slashes, and pairs entries by order, so keep both in `question_id` order. `predict_dev.json` maps each question's position to its predicted query, a tab, `----- bird -----`, a tab and the `db_id`. `dev_gold.sql` has one line per question: the gold query with its line breaks replaced by spaces, a tab and the `db_id`. The dataset's own JSON file at the pinned revision, `data/dev_20251106-00000-of-00001.json`, supplies the difficulty labels. The script prints EX for simple, moderate and challenging questions and overall.

```sh
python evaluation.py --predicted_sql_path predictions/ --ground_truth_path gold/ --data_mode dev \
  --db_root_path dev_databases/ --diff_json_path dev_20251106-00000-of-00001.json --num_cpus 16 --meta_time_out 30.0
```
