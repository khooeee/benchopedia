"""Run a model on a benchmark's tasks and record every attempt.

    python3 runner/run.py gsm8k --model qwen3.6-35b-a3b --profile thinking \\
        --run-id 2026-11-19-qwen3.6-35b-a3b-thinking

Writes data/<benchmark>/runs/<run-id>/:

    run.json       model, settings, commit, environment and the commands to reproduce it
    code/          a copy of every file the runner read: itself, eval.py, the model
    results.jsonl  one line per task, written once all its attempts are graded

The runner refuses uncommitted code, so a run's commit and code copy say exactly
what ran. Run the same command again to resume an interrupted run; the runner
refuses if the code, model or Ollama version changed in between. --scratch writes to
build/scratch-runs/ instead, allows uncommitted code and --limit, and is never published.
Only Python's standard library is required.
"""

import argparse
import importlib.util
import json
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


def load_eval(path):
    spec = importlib.util.spec_from_file_location(f"eval_{path.parent.name.replace('-', '_')}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def environment(model):
    def sysctl(name):
        return subprocess.run(["sysctl", "-n", name], capture_output=True, text=True).stdout.strip()

    machine = platform.machine()
    if platform.system() == "Darwin":
        machine = f"{sysctl('machdep.cpu.brand_string')}, {int(sysctl('hw.memsize')) // 2**30} GB"
        system = f"macOS {platform.mac_ver()[0]}"
    else:
        system = platform.platform()
    return {
        "ollama_version": ollama_api.version(),
        "weights_digest": ollama_api.digest(model["provider_model"]),
        "system": system,
        "machine": machine,
        "python": platform.python_version(),
    }


def repository_url():
    url = git("remote", "get-url", "origin").strip()
    match = re.fullmatch(r"git@github\.com:(.+?)(?:\.git)?", url)
    return f"https://github.com/{match[1]}.git" if match else url


def commands(model, commit, argv, attempts):
    digest = model["weights_digest"]
    return [
        {"command": f"git clone {repository_url()} benchopedia && cd benchopedia && git checkout {commit}",
         "purpose": "Get the exact code and model definition this run used."},
        {"command": f"ollama pull {model['provider_model']}",
         "purpose": f"Download the model. ollama list must show ID {digest[7:19]}, "
                    f"the start of the pinned digest {digest}; a different ID means different weights."},
        {"command": "ollama serve",
         "purpose": "Start Ollama, unless its app is already running. The run's environment lists the version used."},
        {"command": "python3 runner/run.py " + shlex.join(argv),
         "purpose": f"Send every selected task to the model {attempts} times and grade each answer. "
                    "Running the same command again resumes an interrupted run."},
        {"command": "python3 scripts/build_site.py",
         "purpose": "Load the results into SQLite, check them, and generate the website."},
    ]


def select_tasks(runs_dir, tasks, after_runs):
    """Every task, or only those that none of the earlier runs passed."""
    passed = set()
    for run_id in after_runs:
        earlier = runs_dir / run_id
        run = json.loads((earlier / "run.json").read_text(encoding="utf-8"))
        if not run.get("finished_at"):
            raise SystemExit(f"{earlier}: has not finished, so its open tasks are not known yet")
        passed |= {line["key"] for line in read_jsonl(earlier / "results.jsonl") if line["result"] == "pass"}
    return [task for task in tasks if task["key"] not in passed]


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


def attempt_task(task, evaluation, model, profile):
    attempts = []
    for number in range(1, evaluation.ATTEMPTS + 1):
        started_at = now()
        request, response, latency_ms, output = ollama_api.chat(
            model["provider_model"], evaluation.messages(task), profile, seed=number)
        verdict, answer = evaluation.grade(task, output)
        attempts.append({
            "number": number, "verdict": verdict, "output": output, "answer": answer,
            "started_at": started_at,
            "model_calls": [{"number": 1, "request": request, "response": response, "latency_ms": latency_ms}],
        })
    result = "pass" if all(a["verdict"] == "pass" for a in attempts) else "fail"
    return {"key": task["key"], "result": result, "attempts": attempts}


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("benchmark")
    parser.add_argument("--model", required=True, help="a model id from models/")
    parser.add_argument("--profile", required=True, help="one of the model's profiles")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--after", action="append", default=[], metavar="RUN_ID",
                        help="only run tasks this earlier run did not pass; repeatable")
    parser.add_argument("--parallel", type=int, default=1, help="tasks to run at once")
    parser.add_argument("--scratch", action="store_true", help="write to build/scratch-runs/ instead")
    parser.add_argument("--limit", type=int, help="only the first N selected tasks; needs --scratch")
    args = parser.parse_args()
    if args.limit is not None and not args.scratch:
        parser.error("--limit needs --scratch: a published run covers every task it selects")
    if not RUN_ID.fullmatch(args.run_id):
        parser.error("--run-id must use lowercase letters, digits, dots and hyphens")

    benchmark_dir = ROOT / "data" / args.benchmark
    model_file = ROOT / "models" / f"{args.model}.json"
    model = json.loads(model_file.read_text(encoding="utf-8"))
    profile = model["profiles"].get(args.profile)
    if profile is None:
        parser.error(f"{model_file.relative_to(ROOT)} has no profile {args.profile!r}")
    eval_file = benchmark_dir / "eval.py"
    evaluation = load_eval(eval_file)
    files = [Path(__file__).resolve(), Path(ollama_api.__file__).resolve(), eval_file, model_file]
    paths = [str(f.relative_to(ROOT)) for f in files]

    if not args.scratch:
        untracked = set(paths) - set(git("ls-files", "--", *paths).splitlines())
        if untracked or git("status", "--porcelain", "--", *paths).strip():
            raise SystemExit("Commit these files before a published run, or use --scratch: " + ", ".join(paths))
    commit = git("rev-parse", "HEAD").strip()
    env = environment(model)
    if env["weights_digest"] != model["weights_digest"]:
        raise SystemExit(f"Ollama's {model['provider_model']} has digest {env['weights_digest']}, "
                         f"but {model_file.relative_to(ROOT)} pins {model['weights_digest']}")

    runs_dir = ROOT / "build" / "scratch-runs" / args.benchmark if args.scratch else benchmark_dir / "runs"
    run_dir = runs_dir / args.run_id
    run_file = run_dir / "run.json"
    settings = {"model_id": args.model, "profile": args.profile, "settings": profile,
                "attempts_per_task": evaluation.ATTEMPTS, "after_runs": args.after}
    if run_file.exists():
        run = json.loads(run_file.read_text(encoding="utf-8"))
        if run["finished_at"]:
            raise SystemExit(f"{run_dir} has already finished")
        changed = [k for k, v in settings.items() if run[k] != v]
        changed += [p for p, f in zip(paths, files)
                    if (run_dir / "code" / p).read_bytes() != f.read_bytes()]
        changed += [k for k in ("ollama_version", "weights_digest") if run["environment"][k] != env[k]]
        if changed:
            raise SystemExit(f"Cannot resume {run_dir}: changed since it started: {', '.join(changed)}")
        print(f"Resuming {run_dir}")
    else:
        for path, source in zip(paths, files):
            target = run_dir / "code" / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(source.read_bytes())
        run = settings | {"commit_sha": commit, "environment": env,
                          "commands": commands(model, commit, sys.argv[1:], evaluation.ATTEMPTS),
                          "started_at": now(), "finished_at": None}
        run_file.write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    tasks = select_tasks(runs_dir, read_jsonl(benchmark_dir / "tasks.jsonl"), args.after)
    if args.limit is not None:
        tasks = tasks[:args.limit]
    results_file = run_dir / "results.jsonl"
    done = completed_keys(results_file)
    pending = [task for task in tasks if task["key"] not in done]
    print(f"{len(tasks)} tasks selected, {len(done)} already done, {len(pending)} to run", flush=True)

    lock = threading.Lock()
    counts = {"pass": 0, "fail": 0}

    def run_one(task):
        record = attempt_task(task, evaluation, model, profile)
        with lock:
            # Ollama must not change mid-run: an update restarts it with another version.
            if ollama_api.version() != env["ollama_version"]:
                raise SystemExit("Ollama's version changed during the run; the last task was not saved")
            with results_file.open("a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            counts[record["result"]] += 1
            seconds = sum(c["latency_ms"] for a in record["attempts"] for c in a["model_calls"]) / 1000
            verdicts = " ".join(a["verdict"] for a in record["attempts"])
            print(f"[{len(done) + sum(counts.values())}/{len(tasks)}] {task['key']} {record['result']} "
                  f"({verdicts}) {seconds:.0f}s", flush=True)

    pool = ThreadPoolExecutor(max_workers=args.parallel)
    try:
        for future in [pool.submit(run_one, task) for task in pending]:
            future.result()
    finally:
        # On failure, let tasks already sent to the model finish, but start no more.
        pool.shutdown(wait=True, cancel_futures=True)

    # Sort the finished results so the file is stable however the tasks interleaved.
    records = sorted(read_jsonl(results_file) if results_file.exists() else [], key=lambda r: r["key"])
    temporary = results_file.with_suffix(".jsonl.tmp")
    with temporary.open("w", encoding="utf-8", newline="\n") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    temporary.replace(results_file)
    run["finished_at"] = now()
    run_file.write_text(json.dumps(run, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    passed = sum(r["result"] == "pass" for r in records)
    print(f"Finished {run_dir}: {passed} of {len(records)} tasks passed")


if __name__ == "__main__":
    main()
