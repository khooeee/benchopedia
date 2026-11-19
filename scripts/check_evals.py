"""Check each benchmark's eval.py and re-grade every recorded run with the code it ran.

For data/<id>/eval.py, every task must produce chat messages, and grade() must
pass every reference solution. For each run under data/<id>/runs/, the copy of
eval.py the run kept must reproduce each attempt's prompt and verdict from the
recorded model output, and that output must be what the model returned.
"""

import importlib.util
import json
from pathlib import Path

from helpers.build_sqlite import read_results

ROOT = Path(__file__).resolve().parent.parent
VERDICTS = {"pass", "fail", "unparseable"}


def read_jsonl(path):
    with path.open(encoding="utf-8", newline="") as f:
        return [json.loads(line) for line in f]


def load_eval(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_eval(evaluation, tasks, origin, errors):
    if type(evaluation.ATTEMPTS) is not int or evaluation.ATTEMPTS < 1:
        errors.append(f"{origin}: ATTEMPTS must be a positive integer")
    graded = 0
    for task in tasks:
        messages = evaluation.messages(task)
        if (not isinstance(messages, list) or not messages
                or not all(isinstance(m, dict) and isinstance(m.get("role"), str)
                           and isinstance(m.get("content"), str) for m in messages)):
            errors.append(f"{origin}: messages() returned an invalid conversation for {task['key']}")
        if task.get("solution") is None:
            continue
        graded += 1
        verdict, answer = evaluation.grade(task, task["solution"])
        if verdict != "pass":
            errors.append(f"{origin}: grade() gives {verdict} ({answer!r}) for the reference "
                          f"solution of {task['key']}")
    return graded


def check_run(run_dir, tasks, errors):
    benchmark_id = run_dir.parent.parent.name
    copy = run_dir / "code" / "data" / benchmark_id / "eval.py"
    if not copy.is_file():
        errors.append(f"{copy.relative_to(ROOT)}: missing")
        return 0
    evaluation = load_eval(copy, f"run_eval_{benchmark_id}_{run_dir.name}".replace("-", "_").replace(".", "_"))
    by_key = {task["key"]: task for task in tasks}
    results_file = run_dir / "results.jsonl"
    attempts = 0
    for record in read_results(run_dir):
        task = by_key.get(record["key"])
        if task is None:
            errors.append(f"{results_file.relative_to(ROOT)}: unknown task {record['key']}")
            continue
        for attempt in record["attempts"]:
            where = f"{results_file.relative_to(ROOT)}: {record['key']} attempt {attempt['number']}"
            attempts += 1
            calls = attempt["model_calls"]
            if calls and calls[0]["request"].get("messages") != evaluation.messages(task):
                errors.append(f"{where}: the request does not carry the prompt eval.py builds")
            if calls and calls[-1]["response"].get("message", {}).get("content") != attempt["output"]:
                errors.append(f"{where}: output differs from the model's final response")
            regraded = list(evaluation.grade(task, attempt["output"]))
            if regraded != [attempt["verdict"], attempt["answer"]]:
                errors.append(f"{where}: recorded {attempt['verdict']} ({attempt['answer']!r}), "
                              f"but eval.py grades it {regraded[0]} ({regraded[1]!r})")
    return attempts


def main():
    errors = []
    summary = []
    for eval_file in sorted((ROOT / "data").glob("*/eval.py")):
        benchmark_dir = eval_file.parent
        tasks = read_jsonl(benchmark_dir / "tasks.jsonl")
        evaluation = load_eval(eval_file, f"eval_{benchmark_dir.name}".replace("-", "_"))
        graded = check_eval(evaluation, tasks, eval_file.relative_to(ROOT), errors)
        summary.append(f"{benchmark_dir.name}: {graded:,} reference solutions pass")
    for run_dir in sorted(p for p in (ROOT / "data").glob("*/runs/*") if p.is_dir()):
        tasks = read_jsonl(run_dir.parent.parent / "tasks.jsonl")
        attempts = check_run(run_dir, tasks, errors)
        summary.append(f"{run_dir.parent.parent.name}/{run_dir.name}: {attempts:,} attempts re-graded")
    if errors:
        raise SystemExit("\n".join(errors))
    print("OK: " + ("; ".join(summary) if summary else "no eval.py files"))


if __name__ == "__main__":
    main()
