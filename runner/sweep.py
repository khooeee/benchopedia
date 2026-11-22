"""Select and evaluate unresolved benchmark tasks using OpenRouter."""

import argparse
from contextlib import closing
from itertools import takewhile
import json
import sqlite3
import sys
import time
from uuid import uuid4

import checkpoint
import openrouter_api
import run

ROOT = run.ROOT
sys.path.insert(0, str(ROOT / "scripts"))
from helpers.build_sqlite import build_database, load_run, read_results

OPENROUTER_MODEL = ROOT / "runner/models/nemotron-3-ultra-550b-a55b-free.json"
OPENROUTER_PROFILE = "scratch"
BATCH_SIZE = 100


def imported_benchmarks():
    return {path.parent.name for path in (ROOT / "data").glob("*/benchmark.json")
            if path.is_file() and (path.parent / "tasks.jsonl").is_file()
            and not (path.parent / "exclusions.md").exists()}


def exclude_ineligible_tasks(db, benchmarks):
    db.execute("""CREATE TEMP TABLE sweep_excluded (
        benchmark_id TEXT, task_key TEXT, PRIMARY KEY (benchmark_id, task_key))""")
    for benchmark_id in sorted(benchmarks):
        directory = ROOT / "data" / benchmark_id
        evaluation = run.load_eval(directory / "eval.py")
        is_eligible = getattr(evaluation, "is_eligible", None)
        if is_eligible is not None:
            excluded = ((benchmark_id, task["key"]) for task in run.read_jsonl(directory / "tasks.jsonl")
                        if not is_eligible(task))
            db.executemany("INSERT INTO sweep_excluded VALUES (?, ?)", excluded)


def work(db, model, profile, limit, *, verify_grader=False):
    return db.execute("""
        SELECT s.benchmark_id, s.task_key, s.status
        FROM task_status s
        WHERE (:verify_grader OR s.status NOT IN ('solved', 'scored'))
          AND NOT EXISTS (
            SELECT 1 FROM sweep_excluded e WHERE e.benchmark_id = s.benchmark_id
              AND e.task_key = s.task_key
          )
          AND NOT EXISTS (
            SELECT 1 FROM sweep_done d WHERE d.benchmark_id = s.benchmark_id
              AND d.task_key = s.task_key
          )
        ORDER BY CASE WHEN :verify_grader OR s.status = 'untested' THEN 0
                      WHEN s.status = 'pending' THEN 1 ELSE 2 END,
                 CASE WHEN NOT :verify_grader AND s.status = 'open' AND EXISTS (
                    SELECT 1 FROM run_task rt
                    JOIN run r ON r.benchmark_id = rt.benchmark_id AND r.id = rt.run_id
                    JOIN model m ON m.id = r.model_id
                    JOIN benchmark b ON b.id = rt.benchmark_id
                    WHERE rt.benchmark_id = s.benchmark_id AND rt.task_key = s.task_key
                      AND (r.dataset_revision IS NULL OR r.dataset_revision = b.dataset_revision)
                      AND m.provider = :provider AND m.provider_model = :model
                      AND r.profile = :profile
                 ) THEN 1 ELSE 0 END,
                 s.benchmark_id, s.task_key
        LIMIT :limit
    """, {"provider": model["provider"], "model": model["provider_model"],
           "profile": profile, "limit": limit,
           "verify_grader": verify_grader})


def run_openrouter(arguments):
    for retry in (True, False):
        try:
            run.main(arguments)
            return True
        except openrouter_api.RateLimited as error:
            if error.daily or openrouter_api.free_requests_remaining() == 0:
                return False
            if not retry or (error.retry_after is not None and error.retry_after > 60):
                raise
            time.sleep(error.retry_after if error.retry_after is not None else openrouter_api.FREE_INTERVAL)


def evaluate(db, hosted, limit, *, verify_grader=False):
    completed = 0
    while limit is None or completed < limit:
        size = BATCH_SIZE if limit is None else min(BATCH_SIZE, limit - completed)
        selected = iter(work(db, hosted, OPENROUTER_PROFILE, size, verify_grader=verify_grader))
        first = next(selected, None)
        if first is None:
            break
        if openrouter_api.free_requests_remaining() == 0:
            print("OpenRouter daily quota exhausted. Ending the sweep.", flush=True)
            break
        benchmark_id = first["benchmark_id"]
        rows = [first, *takewhile(lambda row: row["benchmark_id"] == benchmark_id, selected)]
        run_id = f"sweep-openrouter-{uuid4().hex[:12]}"
        arguments = [benchmark_id, "--scratch", "--run-id", run_id, "--profile", OPENROUTER_PROFILE,
                     "--scratch-model", str(OPENROUTER_MODEL)]
        for row in rows:
            arguments.extend(["--task-key", row["task_key"]])
        directory = ROOT / "build" / "scratch-runs" / benchmark_id / run_id
        finished = run_openrouter(arguments)
        results = read_results(directory)
        completed += len(results)
        if not finished:
            print(f"OpenRouter daily quota exhausted. Resume from the command in {directory / 'run.json'}.",
                  flush=True)
            break
        errors = []
        load_run(db, benchmark_id, directory, errors, local=True)
        if errors:
            raise SystemExit("\n".join(errors))
        db.executemany("INSERT INTO sweep_done VALUES (?, ?)", [(benchmark_id, row["key"]) for row in results])
    print(f"{completed:,} task evaluations completed.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmarks", nargs="*", help="benchmark IDs to include")
    parser.add_argument("--all", action="store_true", help="include all benchmarks with a grader")
    parser.add_argument("--limit", type=int, help="maximum number of task evaluations")
    parser.add_argument("--verify-grader", action="store_true",
                        help="try tasks from one benchmark, including solved tasks (default: two)")
    parser.add_argument("--dry-run", action="store_true", help="show the priority order without model calls")
    args = parser.parse_args(argv)
    if bool(args.benchmarks) == args.all:
        parser.error("choose benchmark IDs or --all")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    if args.verify_grader and len(args.benchmarks) != 1:
        parser.error("--verify-grader needs exactly one benchmark")
    limit = args.limit or (2 if args.verify_grader else None)
    imported = imported_benchmarks()
    ready = {name for name in imported if (ROOT / "data" / name / "eval.py").is_file()}
    if args.all:
        scope = ready
        skipped = imported - ready
        if skipped:
            print("No sweep evaluator (eval.py) for " + ", ".join(sorted(skipped))
                  + ". Skipping these benchmarks.", file=sys.stderr)
    else:
        scope = set(args.benchmarks)
        unavailable = scope - ready
        if unavailable:
            reasons = [
                f"{name} ({'missing eval.py' if name in imported else 'no imported tasks'})"
                for name in sorted(unavailable)
            ]
            parser.error("cannot evaluate " + ", ".join(reasons))
    for name in sorted(scope):
        evaluation = run.load_eval(ROOT / "data" / name / "eval.py")
        check_setup = getattr(evaluation, "check_setup", None)
        if check_setup is None:
            continue
        error = check_setup()
        if error:
            if not args.all:
                parser.error(f"cannot evaluate {name} ({error})")
            print(f"Skipping {name} ({error})", file=sys.stderr)
            scope.remove(name)
    restored = checkpoint.restore_sweep_runs()
    if restored:
        print(f"Restored {restored} committed sweep run(s) into build/scratch-runs/.", file=sys.stderr)
    hosted = json.loads(OPENROUTER_MODEL.read_text(encoding="utf-8"))
    with closing(sqlite3.connect(":memory:")) as db:
        build_database(db, include_local=True, benchmarks=scope)
        exclude_ineligible_tasks(db, scope)
        db.execute("""CREATE TEMP TABLE sweep_done (
            benchmark_id TEXT, task_key TEXT, PRIMARY KEY (benchmark_id, task_key))""")
        if args.dry_run:
            for row in work(db, hosted, OPENROUTER_PROFILE, limit or -1, verify_grader=args.verify_grader):
                print(f"{row['status']}\t{row['benchmark_id']}\t{row['task_key']}")
        else:
            evaluate(db, hosted, limit, verify_grader=args.verify_grader)


if __name__ == "__main__":
    main()
