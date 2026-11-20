"""Run a model on a benchmark's tasks and record every attempt.

    python3 runner/run.py gsm8k --model qwen3.6-35b-a3b --profile thinking \\
        --run-id 2026-11-19-qwen3.6-35b-a3b-thinking

Writes data/<benchmark>/runs/<run-id>/:

    run.json       model, settings, commit, environment and the commands to reproduce it
    code/          a copy of every file the runner read: itself, eval.py, the model
    results.jsonl  one line per task, written once all its attempts are graded

The runner refuses uncommitted code, so a run's commit and code copy say exactly
what ran. Run the same command again to resume an interrupted run; the runner
refuses if the code, model or Ollama version changed in between. To end a run
early instead, stop the runner and record why with runner/stop.py. --scratch writes to
build/scratch-runs/ instead, allows uncommitted code and --limit, and is never published.
Scratch runs record their selected keys and save unfinished model exchanges in partial/.
Only Python's standard library is required.
"""

import argparse
import hashlib
import importlib.util
import json
import math
import platform
import re
import shlex
import subprocess
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import ollama_api

ROOT = Path(__file__).resolve().parent.parent
RUN_ID = re.compile(r"[a-z0-9][a-z0-9.-]*")


def now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def git(*args):
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout


def read_jsonl(path):
    # Iterate physical lines; Unicode line separators can occur inside text.
    with path.open(encoding="utf-8", newline="") as f:
        return [json.loads(line) for line in f]


def write_json(path, value):
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def load_eval(path):
    spec = importlib.util.spec_from_file_location(f"eval_{path.parent.name.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def environment(model, backend):
    def sysctl(name):
        return subprocess.run(["sysctl", "-n", name], capture_output=True, text=True).stdout.strip()

    machine = platform.machine()
    if platform.system() == "Darwin":
        machine = f"{sysctl('machdep.cpu.brand_string')}, {int(sysctl('hw.memsize')) // 2**30} GB"
        system = f"macOS {platform.mac_ver()[0]}"
    else:
        system = platform.platform()
    host = {
        "system": system,
        "machine": machine,
        "python": platform.python_version(),
    }
    if backend is ollama_api:
        return host | {
            "ollama_version": ollama_api.version(),
            "weights_digest": ollama_api.digest(model["provider_model"]),
        }
    return host | {"provider": model["provider"], "endpoint": backend.CHAT_URL}


def repository_url():
    url = git("remote", "get-url", "origin").strip()
    match = re.fullmatch(r"git@github\.com:(.+?)(?:\.git)?", url)
    return f"https://github.com/{match[1]}.git" if match else url


def commands(model, commit, argv, attempts):
    steps = [
        {"command": f"git clone {repository_url()} benchopedia && cd benchopedia && git checkout {commit}",
         "purpose": "Get the exact code and model definition this run used."},
    ]
    if model["provider"] == "ollama":
        digest = model["weights_digest"]
        steps.extend([
            {"command": f"ollama pull {model['provider_model']}",
             "purpose": f"Download the model. ollama list must show ID {digest[7:19]}, "
                        f"the start of the pinned digest {digest}; a different ID means different weights."},
            {"command": "ollama serve",
             "purpose": "Start Ollama, unless its app is already running. The run's environment lists the version used."},
        ])
    else:
        steps.append({"command": 'test -n "$OPENROUTER_API_KEY" || test -f .env',
                      "purpose": "Configure an OpenRouter key outside the recorded run data."})
    steps.append(
        {"command": "python3 runner/run.py " + shlex.join(argv),
         "purpose": f"Send every selected task to the model {attempts} times and grade each answer. "
                    "Running the same command again resumes an interrupted run."}
    )
    if model["provider"] == "ollama":
        steps.append({"command": "python3 scripts/build_site.py",
                      "purpose": "Load the results into SQLite, check them, and generate the website."})
    return steps


def select_tasks(runs_dir, tasks, after_runs, task_keys=()):
    """Choose eligible tasks, in the requested key order when supplied."""
    passed = set()
    for run_id in after_runs:
        earlier = runs_dir / run_id
        run = json.loads((earlier / "run.json").read_text(encoding="utf-8"))
        if not run.get("finished_at") and not run.get("stopped_at"):
            raise SystemExit(f"{earlier}: is still running, so its open tasks are not known yet")
        passed |= {line["key"] for line in read_jsonl(earlier / "results.jsonl") if line["result"] == "pass"}
    eligible = {task["key"]: task for task in tasks if task["key"] not in passed}
    if not task_keys:
        return list(eligible.values())
    if len(task_keys) != len(set(task_keys)):
        raise SystemExit("--task-key must name each task at most once")
    missing = [key for key in task_keys if key not in eligible]
    if missing:
        raise SystemExit("Unknown or excluded task keys: " + ", ".join(missing))
    return [eligible[key] for key in task_keys]


def completed_keys(results_file):
    """Keys already in results.jsonl, dropping a final line cut short by a crash."""
    if not results_file.exists():
        return set()
    text = results_file.read_text(encoding="utf-8")
    lines = text.split("\n")
    complete, partial = lines[:-1], lines[-1]
    if partial:
        print(f"Dropping an incomplete last line from {results_file}", file=sys.stderr)
        results_file.write_text("".join(line + "\n" for line in complete), encoding="utf-8")
    return {json.loads(line)["key"] for line in complete}


def sort_results(results_file):
    """Sort results.jsonl by task key, so the file is stable however the tasks interleaved."""
    records = sorted(read_jsonl(results_file) if results_file.exists() else [], key=lambda r: r["key"])
    temporary = results_file.with_suffix(".jsonl.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    temporary.replace(results_file)
    return records


def grade_output(task, evaluation, output, *, enforce_output_limit=True):
    score = getattr(evaluation, "score", None)
    if score is None:
        verdict, answer = evaluation.grade(task, output)
        return {"verdict": verdict, "answer": answer}

    limit = getattr(evaluation, "MAX_OUTPUT_CHARS", None)
    scores = None if enforce_output_limit and limit is not None and len(output) > limit else score(task, output)
    return numeric_result(task, scores)


def numeric_result(task, scores):
    if scores is None:
        return {"verdict": "unparseable", "answer": None}
    if not isinstance(scores, dict) or not scores or not all(
        isinstance(name, str) and name.strip() and type(value) in (int, float) and math.isfinite(value)
        for name, value in scores.items()
    ):
        raise ValueError(f"{task['key']}: score() must return named finite numbers or None")
    return {"verdict": "scored", "answer": None, "scores": scores}


def next_messages(evaluation, task, outputs):
    plan = getattr(evaluation, "next_messages", None)
    if plan is not None:
        return plan(task, outputs)
    return None if outputs else evaluation.messages(task)


def response_output(response):
    message = response.get("message")
    if message is None:
        message = response["choices"][0]["message"]
    return message.get("content") or ""


def grade_responses(task, evaluation, outputs):
    score_responses = getattr(evaluation, "score_responses", None)
    if score_responses is not None:
        return numeric_result(task, score_responses(task, outputs))
    return grade_output(task, evaluation, outputs[-1])


def attempt_task(task, evaluation, model, profile, backend, checkpoint=None):
    attempts = (json.loads(checkpoint.read_text(encoding="utf-8"))["attempts"]
                if checkpoint and checkpoint.is_file() else [])
    seeds_used = 0
    for number in range(1, evaluation.ATTEMPTS + 1):
        if number > len(attempts):
            attempts.append({"number": number, "started_at": now(), "model_calls": []})
        attempt = attempts[number - 1]
        calls = attempt["model_calls"]
        if "verdict" not in attempt:
            outputs = [response_output(call["response"]) for call in calls]
            while (messages := next_messages(evaluation, task, outputs)) is not None:
                call_number = len(calls) + 1
                request, response, latency_ms, output = backend.chat(
                    model["provider_model"], messages, profile, seed=seeds_used + call_number)
                calls.append({"number": call_number, "request": request,
                              "response": response, "latency_ms": latency_ms})
                outputs.append(output)
                attempt["output"] = output
                if checkpoint:
                    write_json(checkpoint, {"key": task["key"], "attempts": attempts})
            if not outputs:
                raise ValueError(f"{task['key']}: evaluator requested no model calls")
            attempt.update(grade_responses(task, evaluation, outputs))
            if checkpoint:
                write_json(checkpoint, {"key": task["key"], "attempts": attempts})
        seeds_used += len(calls)
    verdicts = {a["verdict"] for a in attempts}
    if verdicts == {"scored"}:
        result = "scored"
    else:
        result = "pass" if verdicts == {"pass"} else "fail"
    return {"key": task["key"], "result": result, "attempts": attempts}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("benchmark")
    model_choices = parser.add_mutually_exclusive_group(required=True)
    model_choices.add_argument("--model", help="a model id from models/")
    model_choices.add_argument("--scratch-model", type=Path, metavar="PATH",
                               help="use a local model configuration; needs --scratch")
    parser.add_argument("--profile", required=True, help="one of the model's profiles")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--after", action="append", default=[], metavar="RUN_ID",
                        help="only run tasks this earlier run did not pass; repeatable")
    parser.add_argument("--parallel", type=int, default=1, help="tasks to run at once")
    parser.add_argument("--scratch", action="store_true", help="write to build/scratch-runs/ instead")
    parser.add_argument("--scratch-eval", type=Path, metavar="PATH",
                        help="use a local evaluator from within the repository; needs --scratch")
    parser.add_argument("--task-key", action="append", default=[], metavar="KEY",
                        help="select an exact task in argument order; repeatable, needs --scratch")
    parser.add_argument("--limit", type=int, help="only the first N selected tasks; needs --scratch")
    argv = sys.argv[1:] if argv is None else argv
    args = parser.parse_args(argv)
    if args.limit is not None and not args.scratch:
        parser.error("--limit needs --scratch: a published run covers every task it selects")
    if args.scratch_eval is not None and not args.scratch:
        parser.error("--scratch-eval needs --scratch")
    if args.scratch_model is not None and not args.scratch:
        parser.error("--scratch-model needs --scratch")
    if args.task_key and not args.scratch:
        parser.error("--task-key needs --scratch")
    if args.task_key and args.limit is not None:
        parser.error("--task-key supplies the selection; use --limit to select a prefix instead")
    if not re.fullmatch(r"[a-z0-9-]+", args.benchmark):
        parser.error("benchmark must be a catalog ID")
    if not RUN_ID.fullmatch(args.run_id):
        parser.error("--run-id must use lowercase letters, digits, dots and hyphens")

    benchmark_dir = ROOT / "data" / args.benchmark
    runs_dir = ROOT / "build" / "scratch-runs" / args.benchmark if args.scratch else benchmark_dir / "runs"
    tasks = select_tasks(runs_dir, read_jsonl(benchmark_dir / "tasks.jsonl"), args.after, args.task_key)
    if args.limit is not None:
        tasks = tasks[:args.limit]
    model_file = (args.scratch_model.resolve() if args.scratch_model is not None
                  else ROOT / "models" / f"{args.model}.json")
    if not model_file.is_relative_to(ROOT) or not model_file.is_file():
        parser.error("the model configuration must be a file within this repository")
    model = json.loads(model_file.read_text(encoding="utf-8"))
    backend = ollama_api
    if model["provider"] == "openrouter" and args.scratch:
        import openrouter_api
        backend = openrouter_api
        backend.api_key()
    elif model["provider"] != "ollama":
        parser.error("OpenRouter is available for scratch runs")
    profile = model["profiles"].get(args.profile)
    if profile is None:
        parser.error(f"{model_file.relative_to(ROOT)} has no profile {args.profile!r}")
    default_eval = benchmark_dir / "eval.py"
    eval_file = default_eval
    if args.scratch_eval is not None:
        eval_file = args.scratch_eval.resolve()
        if not eval_file.is_relative_to(ROOT) or not eval_file.is_file():
            parser.error("--scratch-eval must name a file within this repository")
    evaluation = load_eval(eval_file)
    sources = {
        Path(__file__).resolve().relative_to(ROOT): Path(__file__).resolve(),
        Path("runner/ollama_api.py"): Path(ollama_api.__file__).resolve(),
        default_eval.relative_to(ROOT): eval_file,
        model_file.relative_to(ROOT): model_file,
    }
    for name in getattr(evaluation, "CAPTURE_FILES", ()):
        if not isinstance(name, str):
            parser.error("CAPTURE_FILES must contain file paths")
        path = Path(name)
        if name != path.as_posix() or not all(RUN_ID.fullmatch(part) for part in path.parts):
            parser.error(f"invalid evaluator support file: {name}")
        source = eval_file.parent / path if len(path.parts) == 1 else ROOT / path
        if not source.resolve().is_relative_to(ROOT) or source.is_symlink() or not source.is_file():
            parser.error(f"evaluator support file missing or not a regular file: {name}")
        capture = (benchmark_dir / path).relative_to(ROOT) if len(path.parts) == 1 else path
        if capture in sources:
            parser.error(f"evaluator support file is already captured: {name}")
        try:
            source.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            parser.error(f"evaluator support files must be UTF-8 text: {name}")
        sources[capture] = source
    if backend is not ollama_api:
        sources[Path("runner/openrouter_api.py")] = Path(backend.__file__).resolve()
    paths = [str(path) for path in sources]

    if not args.scratch:
        untracked = set(paths) - set(git("ls-files", "--", *paths).splitlines())
        if untracked or git("status", "--porcelain", "--", *paths).strip():
            raise SystemExit("Commit these files before a published run, or use --scratch: " + ", ".join(paths))
    commit = git("rev-parse", "HEAD").strip()
    env = environment(model, backend)
    if backend is ollama_api and env["weights_digest"] != model["weights_digest"]:
        raise SystemExit(f"Ollama's {model['provider_model']} has digest {env['weights_digest']}, "
                         f"but {model_file.relative_to(ROOT)} pins {model['weights_digest']}")

    run_dir = runs_dir / args.run_id
    run_file = run_dir / "run.json"
    settings = {"model_id": args.model or model["id"], "profile": args.profile, "settings": profile,
                "attempts_per_task": evaluation.ATTEMPTS, "after_runs": args.after}
    if args.scratch_model is not None:
        settings["scratch_model"] = str(model_file.relative_to(ROOT))
    if args.scratch_eval is not None:
        settings["scratch_eval"] = str(eval_file.relative_to(ROOT))
    metadata = json.loads((benchmark_dir / "benchmark.json").read_text(encoding="utf-8"))
    settings["dataset_revision"] = metadata["dataset_revision"]
    if args.scratch:
        settings["selected_tasks"] = [task["key"] for task in tasks]
    if run_file.exists():
        run = json.loads(run_file.read_text(encoding="utf-8"))
        if run["finished_at"]:
            raise SystemExit(f"{run_dir} has already finished")
        if run.get("stopped_at"):
            raise SystemExit(f"{run_dir} was stopped: {run['stop_reason']}\n"
                             f"To try the tasks it did not pass, start a new run with --after {args.run_id}")
        changed = [k for k, v in settings.items() if run.get(k) != v]
        changed += [str(path) for path, source in sources.items()
                    if (run_dir / "code" / path).read_bytes() != source.read_bytes()]
        env_keys = ("ollama_version", "weights_digest") if backend is ollama_api else ("provider", "endpoint")
        changed += [k for k in env_keys if run["environment"].get(k) != env[k]]
        if changed:
            raise SystemExit(f"Cannot resume {run_dir}: changed since it started: {', '.join(changed)}")
        print(f"Resuming {run_dir}")
    else:
        for path, source in sources.items():
            target = run_dir / "code" / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        run = settings | {"commit_sha": commit, "environment": env,
                          "commands": commands(model, commit, argv, evaluation.ATTEMPTS),
                          "started_at": now(), "finished_at": None, "stopped_at": None, "stop_reason": None}
        write_json(run_file, run)

    results_file = run_dir / "results.jsonl"
    done = completed_keys(results_file)
    pending = [task for task in tasks if task["key"] not in done]
    print(f"{len(tasks)} tasks selected, {len(done)} already done, {len(pending)} to run", flush=True)

    lock = threading.Lock()
    counts = {"pass": 0, "fail": 0, "scored": 0}
    partial_dir = run_dir / "partial"
    if args.scratch:
        partial_dir.mkdir(exist_ok=True)

    def run_one(task):
        key_hash = hashlib.sha256(task["key"].encode("utf-8")).hexdigest()
        checkpoint = partial_dir / f"{key_hash}.json" if args.scratch else None
        record = attempt_task(task, evaluation, model, profile, backend, checkpoint)
        with lock:
            # Ollama must not change mid-run: an update restarts it with another version.
            if backend is ollama_api and ollama_api.version() != env["ollama_version"]:
                raise SystemExit("Ollama's version changed during the run; the last task was not saved")
            record["graded_at"] = now()
            with results_file.open("a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            if checkpoint:
                checkpoint.unlink(missing_ok=True)
            counts[record["result"]] += 1
            seconds = sum(c["latency_ms"] for a in record["attempts"] for c in a["model_calls"]) / 1000
            verdicts = " ".join(a["verdict"] for a in record["attempts"])
            print(f"[{len(done) + sum(counts.values())}/{len(tasks)}] {task['key']} {record['result']} "
                  f"({verdicts}) {seconds:.0f}s", flush=True)

    if args.parallel == 1:
        for task in pending:
            run_one(task)
    else:
        pool = ThreadPoolExecutor(max_workers=args.parallel)
        try:
            for future in [pool.submit(run_one, task) for task in pending]:
                future.result()
        finally:
            # On failure, let tasks already sent to the model finish, but start no more.
            pool.shutdown(wait=True, cancel_futures=True)

    records = sort_results(results_file)
    run["finished_at"] = now()
    write_json(run_file, run)
    passed = sum(r["result"] == "pass" for r in records)
    scored = sum(r["result"] == "scored" for r in records)
    if any(getattr(evaluation, name, None) is not None for name in ("score", "score_responses")):
        print(f"Finished {run_dir}: {scored} of {len(records)} tasks scored")
    else:
        print(f"Finished {run_dir}: {passed} of {len(records)} tasks passed")


if __name__ == "__main__":
    main()
