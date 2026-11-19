"""Exercise run loading and the run checks with a fictional benchmark, model and run."""

import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from helpers import build_sqlite

ROOT = Path(__file__).resolve().parent.parent
DIGEST = "sha256:" + "0" * 64
MODEL = {
    "id": "fixture-model", "name": "Fixture Model", "homepage_url": "https://example.org/model",
    "provider": "ollama", "provider_model": "fixture:1", "weights_digest": DIGEST,
    "profiles": {"default": {"think": True, "options": {"temperature": 1.0}}},
}


def attempt(number, verdict="pass", answer="4"):
    output = f"#### {answer}" if answer is not None else "no answer"
    return {
        "number": number, "verdict": verdict, "output": output, "answer": answer,
        "started_at": "2026-11-19T00:00:00Z",
        "model_calls": [{"number": 1, "request": {"messages": []},
                         "response": {"message": {"content": output}}, "latency_ms": 10}],
    }


class RunChecks(unittest.TestCase):
    def setUp(self):
        (ROOT / "build").mkdir(exist_ok=True)
        temporary = tempfile.TemporaryDirectory(dir=ROOT / "build")
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.data = self.root / "data"
        self.models = self.root / "models"
        self.benchmark_dir = self.data / "fixture"
        self.benchmark_dir.mkdir(parents=True)
        self.models.mkdir()
        self.write_benchmark()
        self.write_model(MODEL)
        self.run = {
            "model_id": "fixture-model", "profile": "default",
            "settings": MODEL["profiles"]["default"], "attempts_per_task": 2, "after_runs": [],
            "commit_sha": "a" * 40, "environment": {"weights_digest": DIGEST},
            "commands": [{"command": "python3 runner/run.py fixture", "purpose": "Run it."}],
            "started_at": "2026-11-19T00:00:00Z", "finished_at": "2026-11-19T01:00:00Z",
        }
        self.results = [
            {"key": "task-1", "result": "pass", "attempts": [attempt(1), attempt(2)]},
            {"key": "task-2", "result": "fail", "attempts": [attempt(1), attempt(2, "fail", "5")]},
        ]
        self.write_run("first", self.run, self.results)
        settings = patch.multiple(build_sqlite, ROOT=self.root, DATA_DIR=self.data,
                                  MODELS_DIR=self.models, CHECKS_DIR=ROOT / "checks")
        settings.start()
        self.addCleanup(settings.stop)

    def write_benchmark(self):
        benchmark = {
            "id": "fixture", "name": "Fixture", "summary": "Fixture tasks.",
            "homepage_url": "https://example.org/", "dataset_url": "https://example.org/data",
            "dataset_revision": "fixture", "released_on": "2026-01-01",
            "task_count": 2, "has_solutions": True,
            "overview": "Overview.", "methodology": "Methodology.",
            "scoring": "Scoring.", "limitations": "Limitations.",
            "sources": [{"title": "Source", "url": "https://example.org/data"}],
        }
        (self.benchmark_dir / "benchmark.json").write_text(json.dumps(benchmark))
        (self.benchmark_dir / "redistribution-review.md").write_text("Fixture review.\n")
        (self.benchmark_dir / "how-to-run.md").write_text("Run {{key}}.\n")
        (self.benchmark_dir / "tasks.jsonl").write_text("".join(
            json.dumps({"key": f"task-{n}", "prompt": "What is 2 + 2?", "solution": "#### 4"}) + "\n"
            for n in (1, 2)))

    def write_model(self, model):
        (self.models / f"{model['id']}.json").write_text(json.dumps(model))

    def write_run(self, run_id, run, results, code=("data/fixture/eval.py", "models/fixture-model.json")):
        run_dir = self.benchmark_dir / "runs" / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "run.json").write_text(json.dumps(run))
        (run_dir / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in results))
        for path in code:
            (run_dir / "code" / path).parent.mkdir(parents=True, exist_ok=True)
            (run_dir / "code" / path).write_text("# fixture\n")
        return run_dir

    def build(self):
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        db.executescript((ROOT / "db/schema.sql").read_text())
        errors = []
        build_sqlite.load_models(db, errors)
        build_sqlite.load_benchmark(db, self.benchmark_dir, build_sqlite.load_exclusions(errors), errors)
        build_sqlite.run_checks(db, errors)
        return db, errors

    def assertFails(self, needle):
        _, errors = self.build()
        self.assertTrue(any(needle in error for error in errors), errors)

    def test_valid_run_loads_and_reports_task_status(self):
        db, errors = self.build()
        self.assertEqual(errors, [])
        self.assertEqual(db.execute("SELECT count(*) FROM model_call").fetchone()[0], 4)
        status = dict(db.execute("SELECT task_key, status FROM task_status").fetchall())
        self.assertEqual(status, {"task-1": "solved", "task-2": "open"})

    def test_task_passes_only_when_every_attempt_passes(self):
        self.results[1]["result"] = "pass"
        self.write_run("first", self.run, self.results)
        self.assertFails("checks/run_task_result.sql")

    def test_task_needs_every_required_attempt(self):
        self.results[0]["attempts"].pop()
        self.write_run("first", self.run, self.results)
        self.assertFails("checks/run_task_result.sql")

    def test_finished_run_covers_every_selected_task(self):
        self.write_run("first", self.run, self.results[:1])
        self.assertFails("checks/run_coverage.sql")

    def test_unfinished_run_may_be_partial(self):
        self.write_run("first", self.run | {"finished_at": None}, self.results[:1])
        self.assertEqual(self.build()[1], [])

    def test_run_in_progress_skips_a_line_still_being_written(self):
        run_dir = self.write_run("first", self.run | {"finished_at": None}, self.results)
        with (run_dir / "results.jsonl").open("a") as f:
            f.write('{"key": "task-3", "res')
        db, errors = self.build()
        self.assertEqual(errors, [])
        self.assertEqual(db.execute("SELECT count(*) FROM run_task").fetchone()[0], 2)

    def test_finished_run_cannot_end_in_a_partial_line(self):
        run_dir = self.write_run("first", self.run, self.results)
        with (run_dir / "results.jsonl").open("a") as f:
            f.write('{"key": "task-3", "res')
        with self.assertRaises(json.JSONDecodeError):
            self.build()

    def test_later_run_only_tries_tasks_earlier_runs_left_open(self):
        later = self.run | {"after_runs": ["first"], "started_at": "2026-11-19T02:00:00Z",
                            "finished_at": "2026-11-19T03:00:00Z"}
        self.write_run("second", later, self.results[1:])
        db, errors = self.build()
        self.assertEqual(errors, [])
        self.write_run("second", later, self.results)
        self.assertFails("checks/run_coverage.sql")

    def test_later_run_needs_a_finished_earlier_run(self):
        self.write_run("first", self.run | {"finished_at": None}, self.results)
        later = self.run | {"after_runs": ["first"], "started_at": "2026-11-19T02:00:00Z", "finished_at": None}
        self.write_run("second", later, [])
        self.assertFails("checks/run_after_runs.sql")

    def test_run_keeps_its_eval_code(self):
        run_dir = self.write_run("first", self.run, self.results)
        (run_dir / "code/data/fixture/eval.py").unlink()
        self.assertFails("checks/run_code.sql")

    def test_run_weights_match_the_model(self):
        self.write_run("first", self.run | {"environment": {"weights_digest": "sha256:" + "1" * 64}}, self.results)
        self.assertFails("checks/run_weights.sql")

    def test_attempt_records_its_model_calls(self):
        self.results[0]["attempts"][0]["model_calls"] = []
        self.write_run("first", self.run, self.results)
        self.assertFails("checks/attempt_model_calls.sql")

    def test_unparseable_attempt_has_no_answer(self):
        self.results[1]["attempts"][1] = attempt(2, "unparseable", None)
        self.write_run("first", self.run, self.results)
        self.assertEqual(self.build()[1], [])
        broken = copy.deepcopy(self.results)
        broken[1]["attempts"][1]["answer"] = "5"
        self.write_run("first", self.run, broken)
        self.assertFails("CHECK constraint failed")

    def test_result_is_pass_or_fail(self):
        self.results[0]["result"] = "maybe"
        self.write_run("first", self.run, self.results)
        self.assertFails("CHECK constraint failed")

    def test_results_name_real_tasks(self):
        self.results[1]["key"] = "task-3"
        self.write_run("first", self.run, self.results)
        self.assertFails("FOREIGN KEY constraint failed")

    def test_run_needs_commands(self):
        self.write_run("first", {k: v for k, v in self.run.items() if k != "commands"}, self.results)
        self.assertFails("commands must list the steps")

    def test_model_file_name_is_its_id(self):
        (self.models / "fixture-model.json").rename(self.models / "other.json")
        self.assertFails("id must match the file name")

    def test_excluded_benchmark_cannot_keep_runs(self):
        (self.benchmark_dir / "exclusions.md").write_text(
            "# Fixture\n\n## Since\n\n2026-11-19\n\n## Reason\n\nNot cleared.\n\n## Restore when\n\nCleared.\n")
        benchmark = json.loads((self.benchmark_dir / "benchmark.json").read_text())
        (self.benchmark_dir / "benchmark.json").write_text(
            json.dumps(benchmark | {"task_count": None, "has_solutions": None}))
        (self.benchmark_dir / "tasks.jsonl").unlink()
        (self.benchmark_dir / "how-to-run.md").unlink()
        self.assertFails("runs quote their prompts")


if __name__ == "__main__":
    unittest.main()
