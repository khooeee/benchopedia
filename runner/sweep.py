"""Select and evaluate unresolved benchmark tasks using OpenRouter, then Ollama."""

import argparse
from contextlib import closing
from itertools import takewhile
import json
import sqlite3
import sys
import time
from uuid import uuid4

import openrouter_api
import run
from stop import stop_run

ROOT = run.ROOT
sys.path.insert(0, str(ROOT / "scripts"))
from helpers.build_sqlite import build_database, load_run, read_results

OPENROUTER_MODEL = ROOT / "runner/models/nemotron-3-ultra-550b-a55b-free.json"
BATCH_SIZE = 100


def imported_benchmarks():
    return {path.parent.name for path in (ROOT / "data").glob("*/benchmark.json")
            if path.is_file() and (path.parent / "tasks.jsonl").is_file()
            and not (path.parent / "exclusions.md").exists()}


def work(db, model, profile, limit):
    return db.execute("""
        SELECT s.benchmark_id, s.task_key, s.status
        FROM task_status s
        WHERE s.status <> 'solved'
          AND NOT EXISTS (
            SELECT 1 FROM sweep_done d WHERE d.benchmark_id = s.benchmark_id
              AND d.task_key = s.task_key AND d.provider = :provider
          )
        ORDER BY CASE s.status WHEN 'untested' THEN 0 WHEN 'pending' THEN 1 ELSE 2 END,
                 CASE WHEN s.status = 'open' AND EXISTS (
                    SELECT 1 FROM run_task rt
                    JOIN run r ON r.benchmark_id = rt.benchmark_id AND r.id = rt.run_id
                    JOIN model m ON m.id = r.model_id
                    JOIN benchmark b ON b.id = rt.benchmark_id
                    WHERE rt.benchmark_id = s.benchmark_id AND rt.task_key = s.task_key
                      AND (r.dataset_revision IS NULL OR r.dataset_revision = b.dataset_revision)
                      AND m.provider = :provider AND m.provider_model = :model
                      AND m.weights_digest IS :digest AND r.profile = :profile
                 ) THEN 1 ELSE 0 END,
                 s.benchmark_id, s.task_key
        LIMIT :limit
    """, {"provider": model["provider"], "model": model["provider_model"],
           "digest": model.get("weights_digest"), "profile": profile, "limit": limit})


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


def evaluate(db, hosted, local, local_profile, limit):
    on_openrouter = True
    completed = 0
    while limit is None or completed < limit:
        model, profile = (hosted, "scratch") if on_openrouter else (local, local_profile)
        size = BATCH_SIZE if limit is None else min(BATCH_SIZE, limit - completed)
        selected = iter(work(db, model, profile, size))
        first = next(selected, None)
        if (on_openrouter and (first is not None or work(db, local, local_profile, 1).fetchone() is not None)
                and openrouter_api.free_requests_remaining() == 0):
            print("OpenRouter daily quota exhausted. Continuing on Ollama.", flush=True)
            on_openrouter = False
            continue
        if first is None:
            break
        benchmark_id = first["benchmark_id"]
        rows = [first, *takewhile(lambda row: row["benchmark_id"] == benchmark_id, selected)]
        run_id = f"sweep-{model['provider']}-{uuid4().hex[:12]}"
        arguments = [benchmark_id, "--scratch", "--run-id", run_id, "--profile", profile]
        if on_openrouter:
            arguments.extend(["--scratch-model", str(OPENROUTER_MODEL)])
        else:
            arguments.extend(["--model", local["id"]])
        for row in rows:
            arguments.extend(["--task-key", row["task_key"]])
        directory = ROOT / "build" / "scratch-runs" / benchmark_id / run_id
        if on_openrouter:
            if not run_openrouter(arguments):
                stop_run(directory, "OpenRouter daily free-model quota exhausted")
                print("Continuing on Ollama from the latest task status.", flush=True)
                on_openrouter = False
        else:
            run.main(arguments)

        errors = []
        load_run(db, benchmark_id, directory, errors, local=True)
        if errors:
            raise SystemExit("\n".join(errors))
        results = read_results(directory)
        db.executemany("INSERT INTO sweep_done VALUES (?, ?, ?)",
                       [(benchmark_id, row["key"], model["provider"]) for row in results])
        completed += len(results)
    print(f"{completed:,} task evaluations completed.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("benchmarks", nargs="*", help="benchmark IDs to include")
    parser.add_argument("--all", action="store_true", help="include all benchmarks with a grader")
    parser.add_argument("--limit", type=int, help="maximum number of task evaluations")
    parser.add_argument("--dry-run", action="store_true", help="show the priority order without model calls")
    parser.add_argument("--ollama-model", default="qwen3.6-35b-a3b")
    parser.add_argument("--ollama-profile", default="scratch")
    args = parser.parse_args(argv)
    if bool(args.benchmarks) == args.all:
        parser.error("choose benchmark IDs or --all")
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
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
    hosted = json.loads(OPENROUTER_MODEL.read_text(encoding="utf-8"))
    local_path = ROOT / "models" / f"{args.ollama_model}.json"
    if not run.RUN_ID.fullmatch(args.ollama_model) or not local_path.is_file():
        parser.error("unknown Ollama model: " + args.ollama_model)
    local = json.loads(local_path.read_text(encoding="utf-8"))
    if args.ollama_profile not in local["profiles"]:
        parser.error("unknown Ollama profile: " + args.ollama_profile)
    with closing(sqlite3.connect(":memory:")) as db:
        build_database(db, include_local=True, benchmarks=scope)
        db.execute("""CREATE TEMP TABLE sweep_done (
            benchmark_id TEXT, task_key TEXT, provider TEXT,
            PRIMARY KEY (benchmark_id, task_key, provider))""")
        if args.dry_run:
            for row in work(db, hosted, "scratch", args.limit or -1):
                print(f"{row['status']}\t{row['benchmark_id']}\t{row['task_key']}")
        else:
            evaluate(db, hosted, local, args.ollama_profile, args.limit)


if __name__ == "__main__":
    main()
