"""Exercise benchmark-local exclusion records and task-loading safeguards."""

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from helpers import build_sqlite

ROOT = Path(__file__).resolve().parent.parent
RECORD = """# Fixture task exclusions

## Since

2026-11-15

## Reason

Pending review.

## Restore when

Permission is documented.
"""


class ExclusionChecks(unittest.TestCase):
    def setUp(self):
        (ROOT / "build").mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=ROOT / "build")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.data = self.root / "data"
        self.benchmark_dir = self.data / "fixture"
        self.benchmark_dir.mkdir(parents=True)
        self.record = self.benchmark_dir / "exclusions.md"
        self.tasks = self.benchmark_dir / "tasks.jsonl"
        self.guide = self.benchmark_dir / "how-to-run.md"
        (self.benchmark_dir / "redistribution-review.md").write_text("Fixture review.\n")
        self.guide.write_text("Run {{key}}.\n")
        self.write_metadata()
        self.write_task()
        settings = patch.multiple(build_sqlite, ROOT=self.root, DATA_DIR=self.data)
        settings.start()
        self.addCleanup(settings.stop)
        self.db = sqlite3.connect(":memory:")
        self.addCleanup(self.db.close)
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript((ROOT / "db/schema.sql").read_text())

    def write_metadata(self, excluded=False):
        benchmark = {
            "id": "fixture", "name": "Fixture", "summary": "A fixture task.",
            "homepage_url": "https://example.org/", "dataset_url": "https://example.org/data",
            "dataset_revision": "fixture", "released_on": "2026-01-01",
            "task_count": None if excluded else 1,
            "has_solutions": None if excluded else True,
            "overview": "Overview.", "methodology": "Methodology.",
            "scoring": "Scoring.", "limitations": "Limitations.",
            "sources": [{"title": "Source", "url": "https://example.org/data"}],
        }
        (self.benchmark_dir / "benchmark.json").write_text(json.dumps(benchmark))

    def write_task(self):
        self.tasks.write_text(json.dumps({
            "key": "task-1", "prompt": "Fixture prompt.", "solution": "Reference.",
        }) + "\n")

    def exclude(self):
        self.record.write_text(RECORD)
        self.write_metadata(excluded=True)
        self.tasks.unlink()
        self.guide.unlink()

    def load(self):
        errors = []
        excluded = build_sqlite.load_exclusions(errors)
        build_sqlite.load_benchmark(self.db, self.benchmark_dir, excluded, errors)
        return errors

    def task_count(self):
        return self.db.execute("SELECT count(*) FROM task").fetchone()[0]

    def test_regular_import_needs_no_exclusion_file(self):
        self.assertEqual(self.load(), [])
        self.assertEqual(self.task_count(), 1)

    def test_exclusion_keeps_article_and_omits_tasks(self):
        self.exclude()
        self.assertEqual(self.load(), [])
        self.assertEqual(self.task_count(), 0)
        self.assertEqual(self.db.execute(
            "SELECT task_count, has_solutions FROM benchmark"
        ).fetchone(), (None, None))

    def test_excluded_task_file_is_rejected_without_reading_it(self):
        self.exclude()
        self.tasks.write_text("invalid JSON that must never be loaded")
        self.assertTrue(any("tasks are excluded" in error for error in self.load()))
        self.assertEqual(self.task_count(), 0)

    def test_missing_tasks_need_an_explicit_exclusion(self):
        self.tasks.unlink()
        errors = self.load()
        self.assertTrue(any("missing; record any exclusion" in error for error in errors))
        self.assertTrue(any("data/fixture/exclusions.md" in error for error in errors))

    def test_included_tasks_need_a_how_to_run_guide(self):
        self.guide.unlink()
        self.assertTrue(any("how-to-run.md: missing" in error for error in self.load()))
        self.assertEqual(self.task_count(), 0)

    def test_how_to_run_guide_must_name_the_task(self):
        self.guide.write_text("Run the task.\n")
        self.assertTrue(any("CHECK constraint failed" in error for error in self.load()))

    def test_excluded_tasks_reject_a_how_to_run_guide(self):
        self.exclude()
        self.guide.write_text("Run {{key}}.\n")
        self.assertTrue(any("no task for it to run" in error for error in self.load()))
        self.assertEqual(self.task_count(), 0)

    def test_excluded_metadata_must_have_null_task_fields(self):
        self.record.write_text(RECORD)
        self.assertTrue(any("must be null" in error for error in self.load()))
        self.assertEqual(self.task_count(), 0)

    def test_null_task_fields_require_an_exclusion_file(self):
        self.write_metadata(excluded=True)
        self.tasks.unlink()
        self.assertTrue(any("task_count is required" in error for error in self.load()))

    def test_cleared_exclusion_can_restore_normal_import(self):
        self.exclude()
        self.record.unlink()
        self.write_metadata()
        self.write_task()
        self.guide.write_text("Run {{key}}.\n")
        self.assertEqual(self.load(), [])
        self.assertEqual(self.task_count(), 1)

    def test_invalid_records_fail_and_still_exclude_the_benchmark(self):
        invalid = [
            "", "# Title only\n",
            RECORD.replace("Pending review.", ""),
            RECORD.replace("Permission is documented.", ""),
            RECORD.replace("2026-11-15", "2026-02-30"),
            RECORD.replace("2026-11-15", "20261115"),
            RECORD + "\n## Reason\n\nDuplicate reason.\n",
        ]
        for text in invalid:
            with self.subTest(text=text):
                self.record.write_text(text)
                errors = []
                self.assertEqual(build_sqlite.load_exclusions(errors), {"fixture"})
                self.assertTrue(errors)
                self.assertTrue(all("data/fixture/exclusions.md" in e for e in errors))

    def test_malformed_record_never_allows_tasks_to_load(self):
        self.exclude()
        self.record.write_text("")
        self.write_task()
        self.assertTrue(self.load())
        self.assertEqual(self.task_count(), 0)

    def test_directory_cannot_stand_in_for_a_record(self):
        self.record.mkdir()
        errors = []
        self.assertEqual(build_sqlite.load_exclusions(errors), {"fixture"})
        self.assertTrue(any("must be a Markdown file" in error for error in errors))

    def test_records_are_discovered_independently_for_each_benchmark(self):
        self.record.write_text(RECORD)
        other = self.data / "other"
        other.mkdir()
        (other / "exclusions.md").write_text(RECORD.replace("Fixture", "Other"))
        errors = []
        self.assertEqual(build_sqlite.load_exclusions(errors), {"fixture", "other"})
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
