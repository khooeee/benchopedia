"""Build build/benchopedia.db from data/ and run every check against it.

Two layers of checking:
  1. db/schema.sql constraints, enforced as each row is inserted.
  2. Shared check queries in checks/*.sql. Each is a
     SELECT that returns the rows violating a rule, so a passing check returns nothing.

Exits non-zero if anything fails.
"""

from datetime import date
import json
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data"
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


def load_benchmark(db, benchmark_dir, excluded, errors):
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
    benchmark["sources"] = json.dumps(benchmark.get("sources"), ensure_ascii=False)
    insert(db, "benchmark", benchmark, benchmark_file.relative_to(ROOT), errors)

    tasks_file = benchmark_dir / "tasks.jsonl"
    if benchmark["id"] in excluded:
        # Excluded tasks stay out of the repository so they cannot be republished by accident.
        if tasks_file.exists():
            errors.append(f"{tasks_file.relative_to(ROOT)}: tasks are excluded in "
                          f"{(benchmark_dir / 'exclusions.md').relative_to(ROOT)}; "
                          "delete them or clear the exclusion")
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
    db.executescript((ROOT / "db" / "schema.sql").read_text(encoding="utf-8"))

    errors = []
    excluded = load_exclusions(errors)
    for benchmark_dir in sorted(p for p in DATA_DIR.iterdir() if p.is_dir()):
        load_benchmark(db, benchmark_dir, excluded, errors)
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
