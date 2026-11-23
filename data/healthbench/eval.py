"""Score HealthBench conversations against their pinned physician rubrics."""

from collections import defaultdict
from functools import lru_cache
from hashlib import sha256
from io import BytesIO, TextIOWrapper
import json
from pathlib import Path
import re


ATTEMPTS = 1
JUDGE_MODEL = "gpt-4.1-2025-04-14"
CAPTURE_FILES = ("grader-prompt.json", "setup_eval.py")
DATASET_URL = "https://openaipublic.blob.core.windows.net/simple-evals/healthbench/2025-05-07-06-14-12_oss_eval.jsonl"
DATASET_SHA256 = "e99dd3c6372c10d6fcc5e385c5fae69d0dd40392dae56836ef9493ae324ecd2f"


def source_path():
    root = next(parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists())
    return root / "build" / "healthbench-rubrics.jsonl"


@lru_cache(maxsize=1)
def records():
    payload = source_path().read_bytes()
    if sha256(payload).hexdigest() != DATASET_SHA256:
        raise ValueError("HealthBench's source file has a different checksum.")
    with TextIOWrapper(BytesIO(payload), encoding="utf-8") as stream:
        entries = {entry["prompt_id"]: entry for entry in map(json.loads, stream)}
    if len(entries) != 5_000:
        raise ValueError("The pinned HealthBench split must have 5,000 rubric records.")
    return entries


def check_setup():
    try:
        records()
    except (OSError, ValueError):
        return "Run python3 data/healthbench/setup_eval.py to fetch the pinned rubrics."


@lru_cache(maxsize=1)
def grader_template():
    return json.loads(Path(__file__).with_name(CAPTURE_FILES[0]).read_text(encoding="utf-8"))


def criteria_met(output):
    try:
        reply = json.loads(re.sub(r"^```json\s*|\s*```$", "", output.strip()))
    except json.JSONDecodeError:
        return None
    result = reply.get("criteria_met") if isinstance(reply, dict) else None
    return result if type(result) is bool else None


def accepted_labels(replies):
    return [result for reply in replies if (result := criteria_met(reply)) is not None]


def next_messages(task, outputs):
    entry = records()[task["key"]]
    conversation = entry["prompt"]
    if not outputs:
        return conversation
    index = len(accepted_labels(outputs[1:]))
    if index >= len(entry["rubrics"]):
        return None
    turn_text = "\n\n".join(f"{turn['role']}: {turn['content']}" for turn in conversation)
    turn_text += f"\n\nassistant: {outputs[0]}"
    item = entry["rubrics"][index]
    prompt = grader_template().replace("<<conversation>>", turn_text).replace(
        "<<rubric_item>>", f"[{item['points']}] {item['criterion']}",
    )
    return [{"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}]


def calculate_score(items_and_labels):
    total = sum(item["points"] for item, _ in items_and_labels if item["points"] > 0)
    if total:
        return sum(item["points"] for item, label in items_and_labels if label) / total


def score_responses(task, outputs):
    entry = records()[task["key"]]
    labels = accepted_labels(outputs[1:])
    if len(labels) != len(entry["rubrics"]):
        return None
    pairs = list(zip(entry["rubrics"], labels))
    overall = calculate_score(pairs)
    metrics = {"overall_score": overall} | dict.fromkeys(entry["example_tags"], overall)
    by_tag = defaultdict(list)
    for item, label in pairs:
        for tag in item["tags"]:
            by_tag[tag].append((item, label))
    for tag, tagged_pairs in by_tag.items():
        score = calculate_score(tagged_pairs)
        if score is not None:
            metrics[tag] = score
    return metrics


def reference_responses(task):
    # Use synthetic rubric verdicts for offline validation of the physician reply.
    rubrics = records()[task["key"]]["rubrics"]
    return [task["solution"], *(json.dumps({"criteria_met": item["points"] > 0}) for item in rubrics)]
