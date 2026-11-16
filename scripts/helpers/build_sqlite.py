"""Build build/benchopedia.db from data/ and run every check against it.

Two layers of checking:
  1. schema.sql constraints, enforced as each row is inserted.
  2. Shared check queries in checks/*.sql. Each is a
     SELECT that returns the rows violating a rule, so a passing check returns nothing.

Exits non-zero if anything fails.
"""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
DB_PATH = ROOT / "build" / "benchopedia.db"

MAX_VIOLATIONS_SHOWN = 10


def insert(db, table, row, origin, errors):
    columns = ", ".join(row)
    placeholders = ", ".join("?" for _ in row)
    try:
        db.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})", list(row.values()))
    except sqlite3.Error as e:
        errors.append(f"{origin}: {e}")


def load_benchmark(db, benchmark_dir, errors):
    benchmark_file = benchmark_dir / "benchmark.json"
    benchmark = json.loads(benchmark_file.read_text(encoding="utf-8"))
    if benchmark.get("id") != benchmark_dir.name:
        errors.append(f"{benchmark_file.relative_to(ROOT)}: id must match the directory name")
        return
    benchmark["sources"] = json.dumps(benchmark.get("sources"), ensure_ascii=False)
    insert(db, "benchmark", benchmark, benchmark_file.relative_to(ROOT), errors)

    tasks_file = benchmark_dir / "tasks.jsonl"
    with tasks_file.open(encoding="utf-8", newline="") as f:
        for line_number, line in enumerate(f, start=1):
            task = json.loads(line)
            task["benchmark_id"] = benchmark["id"]
            origin = f"{tasks_file.relative_to(ROOT)}:{line_number}"
            insert(db, "task", task, origin, errors)


def run_checks(db, errors):
    check_files = sorted((ROOT / "checks").glob("*.sql"))
    for check_file in check_files:
        violations = db.execute(check_file.read_text(encoding="utf-8")).fetchall()
        if not violations:
            continue
        errors.append(f"{check_file.relative_to(ROOT)}: {len(violations)} violation(s)")
        for violation in violations[:MAX_VIOLATIONS_SHOWN]:
            errors.append(f"    {dict(violation)}")
    return len(check_files)


def main():
    DB_PATH.parent.mkdir(exist_ok=True)
    DB_PATH.unlink(missing_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript((ROOT / "schema.sql").read_text(encoding="utf-8"))

    errors = []
    for benchmark_dir in sorted(p for p in DATA_DIR.iterdir() if p.is_dir()):
        load_benchmark(db, benchmark_dir, errors)
    db.commit()
    check_count = run_checks(db, errors)

    benchmarks = db.execute("SELECT count(*) FROM benchmark").fetchone()[0]
    tasks = db.execute("SELECT count(*) FROM task").fetchone()[0]
    db.close()

    if errors:
        print("\n".join(errors), file=sys.stderr)
        sys.exit(f"\nFAILED: {len(errors)} problem line(s) above")
    print(f"OK: {benchmarks} benchmark(s), {tasks} task(s), {check_count} check(s) passed")
    print(f"Built {DB_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
