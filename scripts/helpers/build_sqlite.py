"""Build build/benchopedia.db from data/ and models/ and run every check against it.

Runs written by runner/run.py under data/<benchmark>/runs/ load with their benchmark.

Two layers of checking:
  1. db/schema.sql constraints, enforced as each row is inserted.
  2. Shared check queries in checks/*.sql. Each is a
     SELECT that returns the rows violating a rule, so a passing check returns nothing.

Exits non-zero if anything fails.
"""

from datetime import date
import hashlib
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
MODELS_DIR = ROOT / "models"
CHECKS_DIR = ROOT / "checks"
DB_PATH = ROOT / "build" / "benchopedia.db"

MAX_VIOLATIONS_SHOWN = 10
EXCLUSION_SECTIONS = ("Since", "Reason", "Restore when")


def insert(db, table, row, origin, errors):
    columns = ", ".join(row)
    placeholders = ", ".join("?" for _ in row)
    try:
        db.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", list(row.values()))
    except sqlite3.Error as e:
        errors.append(f"{origin}: {e}")


def load_exclusions(errors):
    """Discover and validate each benchmark's optional task-exclusion record."""
    records = sorted(DATA_DIR.glob("*/exclusions.md"))
    for record in records:
        origin = record.relative_to(ROOT)
        if not record.is_file():
            errors.append(f"{origin}: must be a Markdown file")
            continue
        text = record.read_text(encoding="utf-8")
        headings = list(re.finditer(r"^##[ \t]+(.+?)[ \t]*$", text, re.MULTILINE))
        sections = {}
        for index, heading in enumerate(headings):
            name = heading.group(1)
            end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
            if name in EXCLUSION_SECTIONS:
                if name in sections:
                    errors.append(f"{origin}: duplicate ## {name} section")
                sections[name] = text[heading.end():end].strip()
        if any(not sections.get(name) for name in EXCLUSION_SECTIONS):
            errors.append(f"{origin}: requires nonempty ## Since, ## Reason, and ## Restore when sections")
            continue
        since = sections["Since"]
        try:
            if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", since):
                raise ValueError
            date.fromisoformat(since)
        except ValueError:
            errors.append(f"{origin}: ## Since must contain a YYYY-MM-DD date")
    # Even a malformed record excludes the tasks; its errors still fail the build.
    return {record.parent.name for record in records}


def load_benchmark(db, benchmark_dir, excluded, errors, include_local=False):
    benchmark_file = benchmark_dir / "benchmark.json"
    benchmark = json.loads(benchmark_file.read_text(encoding="utf-8"))
    if benchmark.get("id") != benchmark_dir.name:
        errors.append(f"{benchmark_file.relative_to(ROOT)}: id must match the directory name")
        return
    if benchmark["id"] in excluded:
        if benchmark.get("task_count") is not None or benchmark.get("has_solutions") is not None:
            errors.append(f"{benchmark_file.relative_to(ROOT)}: task_count and has_solutions "
                          "must be null while the tasks are excluded")
            return
    elif benchmark.get("task_count") is None:
        errors.append(f"{benchmark_file.relative_to(ROOT)}: task_count is required")
        return
    elif type(benchmark.get("has_solutions")) is not bool:
        errors.append(f"{benchmark_file.relative_to(ROOT)}: has_solutions must be a JSON boolean")
        return
    review_file = benchmark_dir / "redistribution-review.md"
    if not review_file.is_file():
        errors.append(f"{review_file.relative_to(ROOT)}: missing; see docs/adding-a-benchmark.md")
        return
    benchmark["redistribution_review"] = review_file.read_text(encoding="utf-8")
    # The guide's code runs one of the tasks, so it exists exactly when the tasks do.
    guide_file = benchmark_dir / "how-to-run.md"
    if benchmark["id"] in excluded:
        if guide_file.exists():
            errors.append(f"{guide_file.relative_to(ROOT)}: tasks are excluded, so there is no "
                          "task for it to run; delete it or clear the exclusion")
    elif not guide_file.is_file():
        errors.append(f"{guide_file.relative_to(ROOT)}: missing; see docs/adding-a-benchmark.md")
        return
    else:
        benchmark["how_to_run"] = guide_file.read_text(encoding="utf-8")
    benchmark["sources"] = json.dumps(benchmark.get("sources"), ensure_ascii=False)
    insert(db, "benchmark", benchmark, benchmark_file.relative_to(ROOT), errors)

    tasks_file = benchmark_dir / "tasks.jsonl"
    if benchmark["id"] in excluded:
        # Excluded tasks stay out of the repository so they cannot be republished by accident.
        if tasks_file.exists():
            errors.append(f"{tasks_file.relative_to(ROOT)}: tasks are excluded in "
                          f"{(benchmark_dir / 'exclusions.md').relative_to(ROOT)}; "
                          "delete them or clear the exclusion")
        # Run trajectories quote task prompts, so they are excluded with the tasks.
        runs_dir = benchmark_dir / "runs"
        if runs_dir.exists():
            errors.append(f"{runs_dir.relative_to(ROOT)}: tasks are excluded, and runs quote "
                          "their prompts; delete the runs or clear the exclusion")
        return
    if not tasks_file.is_file():
        errors.append(f"{tasks_file.relative_to(ROOT)}: missing; record any exclusion in "
                      f"{(benchmark_dir / 'exclusions.md').relative_to(ROOT)}")
        return
    with tasks_file.open(encoding="utf-8", newline="") as f:
        for line_number, line in enumerate(f, start=1):
            task = json.loads(line)
            task["benchmark_id"] = benchmark["id"]
            origin = f"{tasks_file.relative_to(ROOT)}:{line_number}"
            insert(db, "task", task, origin, errors)
    for run_dir in sorted(p for p in (benchmark_dir / "runs").glob("*") if p.is_dir()):
        load_run(db, benchmark["id"], run_dir, errors)
    if include_local:
        local_dir = ROOT / "build" / "scratch-runs" / benchmark["id"]
        for run_file in sorted(local_dir.glob("*/run.json")):
            load_run(db, benchmark["id"], run_file.parent, errors, local=True)


def read_results(run_dir):
    """Return one record per task line in run_dir/results.jsonl.

    The runner appends a line as each task finishes, so a run in progress may be
    caught mid-write: its last line is skipped until it ends in a newline. A
    finished or stopped run's file is complete, and a broken last line there is an error.
    """
    results_file = run_dir / "results.jsonl"
    if not results_file.exists():
        return []
    run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
    with results_file.open(encoding="utf-8", newline="") as f:
        lines = list(f)
    if lines and not lines[-1].endswith("\n") and not run.get("finished_at") and not run.get("stopped_at"):
        lines.pop()
    return [json.loads(line) for line in lines]


def load_models(db, errors):
    """Load models/<id>.json. Profiles stay in the file; each run records the settings it used."""
    for model_file in sorted(MODELS_DIR.glob("*.json")):
        origin = model_file.relative_to(ROOT)
        model = json.loads(model_file.read_text(encoding="utf-8"))
        if model.get("id") != model_file.stem:
            errors.append(f"{origin}: id must match the file name")
            continue
        profiles = model.pop("profiles", None)
        if not isinstance(profiles, dict) or not profiles:
            errors.append(f"{origin}: profiles must name at least one set of request settings")
            continue
        insert(db, "model", model, origin, errors)


def recorded_revision(benchmark_id, run):
    if run.get("dataset_revision"):
        return run["dataset_revision"]
    commit = run.get("commit_sha", "")
    if re.fullmatch(r"[0-9a-f]{40}", commit):
        historical = subprocess.run(
            ["git", "show", f"{commit}:data/{benchmark_id}/benchmark.json"],
            cwd=ROOT, capture_output=True, text=True,
        )
        if historical.returncode == 0:
            return json.loads(historical.stdout)["dataset_revision"]
    return None


def local_model(db, run_dir, run, errors):
    path = Path(run.pop("scratch_model", f"models/{run['model_id']}.json"))
    if path.is_absolute() or ".." in path.parts:
        errors.append(f"{run_dir.relative_to(ROOT)}/run.json: invalid model source path")
        return None
    source = run_dir / "code" / path
    if not source.is_file():
        errors.append(f"{source.relative_to(ROOT)}: missing model snapshot")
        return None
    model = json.loads(source.read_text(encoding="utf-8"))
    provider = model["provider"]
    name = model["provider_model"]
    digest = model.get("weights_digest")
    identity = json.dumps([provider, name, digest])
    model_id = "local-" + hashlib.sha256(identity.encode()).hexdigest()
    if db.execute("SELECT 1 FROM model WHERE id = ?", (model_id,)).fetchone() is None:
        insert(db, "model", {"id": model_id, "name": model.get("name", name),
                             "homepage_url": model.get("homepage_url", "https://openrouter.ai/" + name),
                             "provider": provider, "provider_model": name, "weights_digest": digest},
               source.relative_to(ROOT), errors)
    return {"model_id": model_id, "model_file": path.as_posix()}


def load_run(db, benchmark_id, run_dir, errors, local=False):
    """Load one run: run.json, the code it copied, and results.jsonl, one task per line."""
    run_file = run_dir / "run.json"
    if not run_file.is_file():
        errors.append(f"{run_file.relative_to(ROOT)}: missing")
        return
    run = json.loads(run_file.read_text(encoding="utf-8"))
    run["dataset_revision"] = recorded_revision(benchmark_id, run)
    run_id = run_dir.name
    if local:
        grader = Path("data") / benchmark_id / "eval.py"
        snapshot = run_dir / "code" / grader
        current = ROOT / grader
        revision = db.execute("SELECT dataset_revision FROM benchmark WHERE id = ?",
                              (benchmark_id,)).fetchone()[0]
        if (run.get("scratch_eval") or run["dataset_revision"] != revision
                or not current.is_file() or not snapshot.is_file()
                or current.read_bytes() != snapshot.read_bytes()):
            return
        model_fields = local_model(db, run_dir, run, errors)
        if model_fields is None:
            return
        run |= model_fields | {"local": 1}
        while db.execute("SELECT 1 FROM run WHERE benchmark_id = ? AND id = ?",
                         (benchmark_id, run_id)).fetchone() is not None:
            run_id = "local." + run_id
    key = {"benchmark_id": benchmark_id, "run_id": run_id}
    commands = run.pop("commands", None)
    for field in ("settings", "after_runs", "environment"):
        run[field] = json.dumps(run.get(field), ensure_ascii=False)
    if run.get("selected_tasks") is not None:
        run["selected_tasks"] = json.dumps(run["selected_tasks"], ensure_ascii=False)
    before = len(errors)
    insert(db, "run", {"benchmark_id": benchmark_id, "id": run_id} | run,
           run_file.relative_to(ROOT), errors)
    if len(errors) > before:
        return
    if not isinstance(commands, list) or not commands:
        errors.append(f"{run_file.relative_to(ROOT)}: commands must list the steps that produced the run")
    for number, command in enumerate(commands or [], start=1):
        insert(db, "run_command", key | {"number": number} | command,
               f"{run_file.relative_to(ROOT)} command {number}", errors)
    code_dir = run_dir / "code"
    for path in sorted(p for p in code_dir.rglob("*") if p.is_file()):
        insert(db, "run_file", key | {"path": path.relative_to(code_dir).as_posix(),
                                      "content": path.read_text(encoding="utf-8")},
               path.relative_to(ROOT), errors)
    records = read_results(run_dir)
    located = [(record, f"{(run_dir / 'results.jsonl').relative_to(ROOT)}:{number}")
               for number, record in enumerate(records, start=1)]
    if local:
        complete = {record["key"] for record in records}
        for checkpoint in sorted((run_dir / "partial").glob("*.json")):
            record = json.loads(checkpoint.read_text(encoding="utf-8"))
            if record["key"] in complete:
                continue
            record["result"] = "pending"
            for attempt in record["attempts"]:
                attempt.setdefault("verdict", "pending")
                attempt.setdefault("answer", None)
            located.append((record, checkpoint.relative_to(ROOT)))
    for result, origin in located:
        task = key | {"task_key": result.pop("key", None)}
        attempts = result.pop("attempts", None)
        insert(db, "run_task", task | result, origin, errors)
        if not isinstance(attempts, list):
            errors.append(f"{origin}: attempts must be a list")
            continue
        for attempt in attempts:
            calls = attempt.pop("model_calls", None)
            if attempt.get("scores") is not None:
                try:
                    attempt["scores"] = json.dumps(attempt["scores"], allow_nan=False)
                except ValueError:
                    errors.append(f"{origin}: attempt scores must be finite")
                    continue
            insert(db, "attempt", task | attempt, origin, errors)
            if not isinstance(calls, list):
                errors.append(f"{origin}: attempt {attempt.get('number')}: model_calls must be a list")
                continue
            for call in calls:
                call = call | {"request": json.dumps(call.get("request"), ensure_ascii=False),
                               "response": json.dumps(call.get("response"), ensure_ascii=False)}
                insert(db, "model_call", task | {"attempt_number": attempt.get("number")} | call,
                       origin, errors)


def run_checks(db, errors):
    check_files = sorted(CHECKS_DIR.glob("*.sql"))
    for check_file in check_files:
        violations = db.execute(check_file.read_text(encoding="utf-8")).fetchall()
        if not violations:
            continue
        errors.append(f"checks/{check_file.name}: {len(violations)} violation(s)")
        for violation in violations[:MAX_VIOLATIONS_SHOWN]:
            errors.append(f"    {dict(violation)}")
    return len(check_files)


def build_database(db, include_local=False, benchmarks=None):
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript((ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))

    errors = []
    excluded = load_exclusions(errors)
    load_models(db, errors)
    for benchmark_dir in sorted(p for p in DATA_DIR.iterdir() if p.is_dir()):
        if benchmarks is None or benchmark_dir.name in benchmarks:
            load_benchmark(db, benchmark_dir, excluded, errors, include_local)
    db.commit()
    check_count = run_checks(db, errors)

    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(f"\nFAILED: {len(errors)} problem line(s) above")
    return check_count


def main(include_local=False, path=None):
    path = DB_PATH if path is None else path
    path.parent.mkdir(exist_ok=True)
    path.unlink(missing_ok=True)
    with sqlite3.connect(path) as db:
        check_count = build_database(db, include_local)
        benchmarks = db.execute("SELECT count(*) FROM benchmark").fetchone()[0]
        tasks = db.execute("SELECT count(*) FROM task").fetchone()[0]
        runs = db.execute("SELECT count(*) FROM run").fetchone()[0]
    print(f"OK: {benchmarks} benchmark(s), {tasks} task(s), {runs} run(s), "
          f"{check_count} check(s) passed")
    print(f"Built {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
