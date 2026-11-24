#!/usr/bin/env python3
"""Import every question in the LogicBench(Eval) binary QA split."""

import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.parse import quote
from urllib.request import urlopen


HERE = Path(__file__).resolve().parent
REPOSITORY = "Mihir3009/LogicBench"
SPLIT = "data/LogicBench(Eval)/BQA"
CHECKSUM = "78fcbe5dc1c81bab10982bb2118c652830184e5e802a45f887e61271caaef58d"
RULES = {
    "first_order_logic": (
        "bidirectional_dilemma", "constructive_dilemma", "destructive_dilemma",
        "disjunctive_syllogism", "existential_generalization", "hypothetical_syllogism",
        "modus_ponens", "modus_tollens", "universal_instantiation",
    ),
    "nm_logic": (
        "default_reasoning_default", "default_reasoning_irr", "default_reasoning_open",
        "default_reasoning_several", "reasoning_about_exceptions_1",
        "reasoning_about_exceptions_2", "reasoning_about_exceptions_3", "reasoning_about_priority",
    ),
    "propositional_logic": (
        "bidirectional_dilemma", "commutation", "constructive_dilemma", "destructive_dilemma",
        "disjunctive_syllogism", "hypothetical_syllogism", "material_implication", "modus_tollens",
    ),
}


def parse_tasks(payload, family, rule, source_url):
    tasks, sample_ids = [], set()
    for sample in json.loads(payload)["samples"]:
        sample_id = sample["id"]
        if type(sample_id) is not int or sample_id in sample_ids:
            raise ValueError(f"{family}/{rule}: invalid or repeated source sample ID {sample_id!r}")
        sample_ids.add(sample_id)
        context = sample["context"]
        pairs = sample["qa_pairs"]
        if not isinstance(context, str) or not context.strip() or not pairs:
            raise ValueError(f"{family}/{rule}/{sample_id}: missing context or questions")
        for position, pair in enumerate(pairs, start=1):
            key = f"{family}.{rule}.{sample_id:02d}.{position}"
            question, answer = pair["question"], pair["answer"]
            if not isinstance(question, str) or not question.strip() or answer not in ("yes", "no"):
                raise ValueError(f"{key}: missing question or binary label")
            tasks.append({
                "key": key,
                "prompt": f"Context: {context}\n\nQuestion: {question}",
                "solution": answer,
                "prompt_source_url": source_url,
                "solution_source_url": source_url,
            })
    if sample_ids != set(range(1, 21)):
        raise ValueError(f"{family}/{rule}: expected all 20 source sample IDs")
    return tasks


def load_tasks(source_dir=None):
    metadata = json.loads((HERE / "benchmark.json").read_text(encoding="utf-8"))
    revision = metadata["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("dataset_revision must identify an immutable GitHub commit")
    tasks = []
    manifest = sha256()
    for family, rules in sorted(RULES.items()):
        for rule in sorted(rules):
            relative = f"{family}/{rule}/data_instances.json"
            source_path = quote(f"{SPLIT}/{relative}")
            if source_dir is None:
                url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/{source_path}"
                with urlopen(url, timeout=30) as response:
                    payload = response.read()
            else:
                payload = (source_dir / relative).read_bytes()
            manifest.update(f"{sha256(payload).hexdigest()}  {relative}\n".encode())
            source_url = f"https://github.com/{REPOSITORY}/blob/{revision}/{source_path}"
            tasks.extend(parse_tasks(payload, family, rule, source_url))
    if manifest.hexdigest() != CHECKSUM:
        raise ValueError("Binary QA file checksums differ from the reviewed release")
    if len({task["key"] for task in tasks}) != len(tasks) or len(tasks) != metadata["task_count"]:
        raise ValueError("Imported task keys or count do not match the complete binary QA split")
    if Counter(task["solution"] for task in tasks) != {"yes": 520, "no": 1000}:
        raise ValueError("Binary QA labels do not match the published split statistics")
    return sorted(tasks, key=lambda task: task["key"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, help="Read the pinned files from a local copy of the BQA directory")
    args = parser.parse_args()
    tasks = load_tasks(args.source_dir)
    with NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", dir=HERE, delete=False) as temporary:
        for task in tasks:
            temporary.write(json.dumps(task, ensure_ascii=False) + "\n")
    Path(temporary.name).replace(HERE / "tasks.jsonl")
    print(f"Imported {len(tasks):,} LogicBench binary questions")


if __name__ == "__main__":
    main()
