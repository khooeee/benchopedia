"""Exercise score validation with fictional records, without upstream data."""

import contextlib
import copy
import io
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from helpers import build_sqlite
from helpers.load_scores import load_scores

ROOT = Path(__file__).resolve().parent.parent
BENCHMARK = {
    "id": "example", "name": "Example", "summary": "Fictional test fixture.",
    "homepage_url": "https://example.org", "dataset_url": "https://example.org/data",
    "dataset_revision": "fixture-v1", "released_on": "2026-01-01", "task_count": 1,
    "has_solutions": False, "overview": "Fixture", "methodology": "Fixture",
    "scoring": "Fixture", "limitations": "Fixture", "sources": [{"title": "Fixture", "url": "https://example.org"}],
}
SNAPSHOT = {
    "metrics": [{"id": "example-resolved", "name": "Resolved", "unit": "percent",
                 "min_value": 0, "max_value": 100, "higher_is_better": True}],
    "setups": [{"id": "example-standard", "metric_id": "example-resolved",
                "dataset_revision": "fixture-v1", "split": "test", "agent": None,
                "configuration": {"tools": None, "attempt_policy": "one attempt", "budget": None},
                "documentation_url": "https://example.org/protocol"}],
    "scores": [{"id": "example-run-1", "setup_id": "example-standard",
                "model_name": "Fictional Model", "value": 72.4,
                "reported_on": "2026-01-02", "observed_on": "2026-01-03",
                "source_url": "https://example.org/results#run-1", "source_revision": "fixture-v1"}],
}


class ScoreChecks(unittest.TestCase):
    def setUp(self):
        (ROOT / "build").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(prefix="score-check-", dir=ROOT / "build")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "scores.json"
        self.db = sqlite3.connect(":memory:")
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.execute("PRAGMA foreign_keys = ON")
        self.db.executescript((ROOT / "db/schema.sql").read_text())
        self.insert_benchmark(BENCHMARK)

    def insert_benchmark(self, benchmark):
        row = dict(benchmark, sources=json.dumps(benchmark["sources"]))
        self.db.execute(f"INSERT INTO benchmark ({', '.join(row)}) VALUES ({', '.join('?' for _ in row)})",
                        list(row.values()))
        self.db.execute("INSERT INTO task (benchmark_id, key, prompt) VALUES (?, 'one', 'Fixture')",
                        (benchmark["id"],))

    def load(self, snapshot=None, benchmark_id="example"):
        self.path.write_text(json.dumps(SNAPSHOT if snapshot is None else snapshot))
        errors = []
        load_scores(self.db, self.path, benchmark_id, errors)
        return errors

    def violations(self):
        errors = []
        build_sqlite.run_checks(self.db, errors)
        return errors

    def test_valid_snapshot_preserves_native_value_and_configuration(self):
        self.assertEqual(self.load(), [])
        self.assertEqual(self.violations(), [])
        self.assertEqual(self.db.execute("SELECT value FROM score").fetchone()[0], 72.4)
        stored = self.db.execute("SELECT configuration FROM evaluation_setup").fetchone()[0]
        self.assertEqual(json.loads(stored), SNAPSHOT["setups"][0]["configuration"])

    def test_missing_snapshot_is_optional(self):
        errors = []
        load_scores(self.db, self.path, "example", errors)
        self.assertEqual(errors, [])
        self.assertEqual(self.db.execute("SELECT count(*) FROM score").fetchone()[0], 0)

    def test_empty_snapshot_is_valid(self):
        self.assertEqual(self.load({"metrics": [], "setups": [], "scores": []}), [])

    def test_repeated_model_runs_and_unknown_reporting_dates_are_allowed(self):
        snapshot = copy.deepcopy(SNAPSHOT)
        second = dict(snapshot["scores"][0], id="example-run-2", value=70, reported_on=None)
        snapshot["scores"].append(second)
        self.assertEqual(self.load(snapshot), [])
        self.assertEqual(self.db.execute("SELECT count(*) FROM score").fetchone()[0], 2)

    def test_bounds_are_checked_inclusive_and_can_be_unbounded(self):
        self.assertEqual(self.load(), [])
        for value, invalid in ((0, False), (100, False), (-0.1, True), (100.1, True)):
            self.db.execute("UPDATE score SET value = ?", (value,))
            self.assertEqual(bool(self.violations()), invalid)
        self.db.execute("UPDATE benchmark_metric SET min_value = NULL, max_value = NULL")
        self.assertEqual(self.violations(), [])

    def test_lower_is_better_metric(self):
        snapshot = copy.deepcopy(SNAPSHOT)
        snapshot["metrics"][0].update(unit="seconds", max_value=None, higher_is_better=False)
        snapshot["scores"][0]["value"] = 120.5
        self.assertEqual(self.load(snapshot), [])
        self.assertEqual(self.violations(), [])

    def test_non_numeric_and_non_finite_scores_fail(self):
        for value in (None, True, "72.4", float("nan"), float("inf"), -float("inf"), 10 ** 400):
            with self.subTest(value=str(value)):
                snapshot = copy.deepcopy(SNAPSHOT)
                snapshot["scores"][0]["value"] = value
                errors = self.load(snapshot)
                self.assertTrue(any("finite" in error or "constant" in error for error in errors))
                self.db.execute("DELETE FROM evaluation_setup")
                self.db.execute("DELETE FROM benchmark_metric")

    def test_malformed_structure_and_unknown_fields_fail_with_origin(self):
        for snapshot in ([], {}, dict(SNAPSHOT, extra=[]), dict(SNAPSHOT, scores={}),
                         dict(SNAPSHOT, scores=[None]),
                         dict(SNAPSHOT, scores=[dict(SNAPSHOT["scores"][0], typo=1)])):
            with self.subTest(snapshot=snapshot):
                errors = self.load(snapshot)
                self.assertTrue(errors)
                self.assertTrue(all(str(self.path) in error for error in errors))
                self.db.execute("DELETE FROM evaluation_setup")
                self.db.execute("DELETE FROM benchmark_metric")

    def test_invalid_json_fails_with_origin(self):
        self.path.write_text('{"metrics":')
        errors = []
        load_scores(self.db, self.path, "example", errors)
        self.assertTrue(errors)
        self.assertIn(str(self.path), errors[0])

    def test_metric_constraints(self):
        for changes in ({"higher_is_better": 1}, {"min_value": True}, {"min_value": "0"},
                        {"min_value": 100, "max_value": 0}, {"min_value": 100, "max_value": 100},
                        {"max_value": float("inf")}, {"unit": ""}, {"benchmark_id": "other"}):
            with self.subTest(changes=changes):
                snapshot = copy.deepcopy(SNAPSHOT)
                snapshot["metrics"][0].update(changes)
                self.assertTrue(self.load(snapshot))

    def test_text_fields_reject_numeric_coercion(self):
        snapshot = copy.deepcopy(SNAPSHOT)
        snapshot["scores"][0]["source_revision"] = 123
        self.assertTrue(any("JSON string" in error for error in self.load(snapshot)))

    def test_dates_and_provenance_are_required_and_valid(self):
        self.assertEqual(self.load(), [])
        invalid = {"reported_on": ["", "garbage", "2026-02-30", "2026-1-02", "2026-01-04"],
                   "observed_on": [None, "garbage", "2025-02-29", "2026-01-01"],
                   "source_url": [None, "http://example.org", ""],
                   "source_revision": [None, " "]}
        for column, values in invalid.items():
            for value in values:
                with self.subTest(column=column, value=value), self.assertRaises(sqlite3.IntegrityError):
                    self.db.execute(f"UPDATE score SET {column} = ?", (value,))
        self.db.execute("UPDATE score SET reported_on = '2024-02-29'")

    def test_url_configuration_and_reference_validation(self):
        for section, changes in (("setups", {"metric_id": "missing"}),
                                 ("setups", {"configuration": "{}"}),
                                 ("setups", {"documentation_url": "https:///missing-host"}),
                                 ("scores", {"setup_id": "missing"}),
                                 ("scores", {"source_url": "https://example.org/a b"})):
            with self.subTest(changes=changes):
                snapshot = copy.deepcopy(SNAPSHOT)
                snapshot[section][0].update(changes)
                self.assertTrue(self.load(snapshot))
                self.db.execute("DELETE FROM evaluation_setup")
                self.db.execute("DELETE FROM benchmark_metric")

    def test_cross_benchmark_references_are_rejected(self):
        self.assertEqual(self.load(), [])
        self.insert_benchmark(dict(BENCHMARK, id="other", name="Other"))
        for snapshot in ({"metrics": [], "setups": [dict(SNAPSHOT["setups"][0], id="other-setup")], "scores": []},
                         {"metrics": [], "setups": [], "scores": [dict(SNAPSHOT["scores"][0], id="other-run")]}):
            self.assertTrue(any("belong" in error for error in self.load(snapshot, "other")))

    def test_duplicate_run_ids_fail_and_foreign_keys_are_active(self):
        snapshot = copy.deepcopy(SNAPSHOT)
        snapshot["scores"].append(snapshot["scores"][0])
        self.assertTrue(any("UNIQUE" in error for error in self.load(snapshot)))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("UPDATE score SET setup_id = 'missing'")

    def test_build_loads_optional_snapshot_and_fails_on_out_of_bounds(self):
        (self.root / "db").mkdir()
        (self.root / "db/schema.sql").write_text((ROOT / "db/schema.sql").read_text())
        (self.root / "checks").mkdir()
        for check in (ROOT / "checks").glob("*.sql"):
            (self.root / "checks" / check.name).write_text(check.read_text())
        benchmark_dir = self.root / "data/example"
        benchmark_dir.mkdir(parents=True)
        (benchmark_dir / "benchmark.json").write_text(json.dumps(BENCHMARK))
        (benchmark_dir / "tasks.jsonl").write_text('{"key":"one","prompt":"Fixture"}\n')
        with patch.multiple(build_sqlite, ROOT=self.root, DATA_DIR=self.root / "data",
                            DB_PATH=self.root / "build/benchopedia.db"):
            with contextlib.redirect_stdout(io.StringIO()):
                build_sqlite.main()  # Existing benchmarks need no scores.json.
                (benchmark_dir / "scores.json").write_text(json.dumps(SNAPSHOT))
                build_sqlite.main()
            with sqlite3.connect(self.root / "build/benchopedia.db") as db:
                self.assertEqual(db.execute("SELECT count(*) FROM score").fetchone()[0], 1)
            snapshot = copy.deepcopy(SNAPSHOT)
            snapshot["scores"][0]["value"] = 101
            (benchmark_dir / "scores.json").write_text(json.dumps(snapshot))
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                build_sqlite.main()


if __name__ == "__main__":
    unittest.main()
