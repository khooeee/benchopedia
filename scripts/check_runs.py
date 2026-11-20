"""Exercise run loading and the run checks with a fictional benchmark, model and run."""

import copy
import io
import json
import sqlite3
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from urllib.error import HTTPError
from unittest.mock import patch

from helpers import build_sqlite

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "runner"))
import stop  # noqa: E402
import run  # noqa: E402
import sweep  # noqa: E402

STOPPED = {"finished_at": None, "stopped_at": "2026-11-19T00:30:00Z", "stop_reason": "Too slow."}
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

    def prepare_runner_fixture(self, extra_tasks=()):
        metadata = self.benchmark_dir / "benchmark.json"
        benchmark = json.loads(metadata.read_text())
        benchmark["task_count"] += len(extra_tasks)
        metadata.write_text(json.dumps(benchmark))
        with (self.benchmark_dir / "tasks.jsonl").open("a") as tasks:
            for key in extra_tasks:
                tasks.write(json.dumps({"key": key, "prompt": "What is 2 + 2?", "solution": "#### 4"}) + "\n")
        (self.benchmark_dir / "eval.py").write_text("""
ATTEMPTS = 2
def messages(task):
    return [{"role": "user", "content": task["key"]}]
def grade(task, output):
    return ("pass" if output == task["solution"] else "fail"), output
""")
        runner = self.root / "runner" / "run.py"
        runner.parent.mkdir()
        runner.write_bytes((ROOT / "runner" / "run.py").read_bytes())
        schema = self.root / "db" / "schema.sql"
        schema.parent.mkdir()
        schema.write_bytes((ROOT / "db" / "schema.sql").read_bytes())
        hosted = runner.parent / "hosted.json"
        hosted.write_bytes(sweep.OPENROUTER_MODEL.read_bytes())
        patches = [
            patch.multiple(run, ROOT=self.root, __file__=str(runner),
                           git=lambda *args: "a" * 40 if args[0] == "rev-parse" else "https://example.org/repo.git"),
            patch.multiple(sweep, ROOT=self.root, OPENROUTER_MODEL=hosted),
            patch.object(run.ollama_api, "version", return_value="fixture"),
            patch.object(run.ollama_api, "digest", return_value=DIGEST),
            patch.object(sweep.openrouter_api, "api_key", return_value="fixture"),
        ]
        for setting in patches:
            setting.start()
            self.addCleanup(setting.stop)

    @staticmethod
    def reply(model, messages, profile, seed, output="#### 4"):
        return ({"model": model, "messages": messages, "seed": seed},
                {"message": {"content": output}}, 10, output)

    def test_exact_selection_resumes_at_saved_attempt(self):
        self.prepare_runner_fixture(("task-3",))
        seen = []

        def chat(model, messages, profile, seed):
            seen.append((messages[0]["content"], seed))
            if len(seen) == 2:
                raise RuntimeError("fixture interruption")
            return self.reply(model, messages, profile, seed)

        args = ["fixture", "--scratch", "--run-id", "selected", "--model", MODEL["id"],
                "--profile", "default", "--task-key", "task-3", "--task-key", "task-1"]
        with patch.object(run.ollama_api, "chat", side_effect=chat), redirect_stdout(io.StringIO()):
            with self.assertRaisesRegex(RuntimeError, "fixture interruption"):
                run.main(args)
            with self.assertRaisesRegex(SystemExit, "selected_tasks"):
                run.main(args[:-1] + ["task-2"])
            run.main(args)
        self.assertEqual(seen, [("task-3", 1), ("task-3", 2), ("task-3", 2), ("task-1", 1), ("task-1", 2)])
        directory = self.root / "build" / "scratch-runs" / "fixture" / "selected"
        self.assertEqual(json.loads((directory / "run.json").read_text())["selected_tasks"], ["task-3", "task-1"])
        self.assertEqual([r["key"] for r in build_sqlite.read_results(directory)], ["task-1", "task-3"])
        with self.assertRaisesRegex(SystemExit, "Unknown"):
            run.main(args[:-1] + ["missing"])
        with self.assertRaisesRegex(SystemExit, "at most once"):
            run.main(args[:-1] + ["task-3"])

    def test_daily_quota_handoff_uses_latest_status_and_preserves_partial_calls(self):
        self.prepare_runner_fixture(("task-3", "task-4"))
        self.write_run("first", self.run | STOPPED, self.results)
        hosted = []
        local = []

        def openrouter_chat(model, messages, profile, seed):
            hosted.append((messages[0]["content"], seed))
            if seed == 2:
                body = b'{"error":{"metadata":{"limit_source":"openrouter_free_tier_daily"}}}'
                error = HTTPError("https://example.org", 429, "quota", {}, io.BytesIO(body))
                raise sweep.openrouter_api.RateLimited(error)
            return self.reply(model, messages, profile, seed, "#### 5")

        def ollama_chat(model, messages, profile, seed):
            local.append((messages[0]["content"], seed))
            return self.reply(model, messages, profile, seed)

        with patch.object(sweep.openrouter_api, "free_requests_remaining", return_value=1):
            with patch.object(sweep.openrouter_api, "chat", side_effect=openrouter_chat):
                with patch.object(run.ollama_api, "chat", side_effect=ollama_chat), redirect_stdout(io.StringIO()):
                    sweep.main(["fixture", "--limit", "3", "--ollama-model", MODEL["id"], "--ollama-profile", "default"])
        self.assertEqual(hosted, [("task-3", 1), ("task-3", 2)])
        self.assertEqual(local, [(task, seed) for task in ("task-4", "task-3", "task-2") for seed in (1, 2)])
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        build_sqlite.build_database(db, include_local=True)
        rows = db.execute("SELECT result, count(*) FROM run_task GROUP BY result")
        self.assertEqual({row[0]: row[1] for row in rows}, {"pass": 4, "fail": 1, "pending": 1})
        self.assertEqual(db.execute("SELECT count(*) FROM task_status WHERE status = 'solved'").fetchone()[0], 4)

    def test_unparseable_attempt_in_completed_evaluation_leaves_task_open(self):
        for first in [attempt(1), attempt(1, "unparseable", None)]:
            with self.subTest(first=first["verdict"]):
                self.results[1]["attempts"] = [first, attempt(2, "unparseable", None)]
                self.write_run("first", self.run, self.results)
                db, errors = self.build()
                self.assertEqual(errors, [])
                status = db.execute("SELECT status FROM task_status WHERE task_key = 'task-2'").fetchone()[0]
                self.assertEqual(status, "open")

    def test_handoff_when_last_hosted_call_uses_the_quota(self):
        self.prepare_runner_fixture()

        def wrong(model, messages, profile, seed):
            return self.reply(model, messages, profile, seed, "#### 5")

        with patch.object(sweep.openrouter_api, "free_requests_remaining", side_effect=[2, 0]):
            with patch.object(sweep.openrouter_api, "chat", side_effect=wrong) as hosted:
                with patch.object(run.ollama_api, "chat", side_effect=self.reply) as local:
                    with redirect_stdout(io.StringIO()):
                        sweep.main(["fixture", "--limit", "2", "--ollama-model", MODEL["id"],
                                    "--ollama-profile", "default"])
        self.assertEqual(hosted.call_count, 2)
        self.assertEqual(local.call_count, 2)
        for call in [*hosted.call_args_list, *local.call_args_list]:
            self.assertEqual(call.args[1][0]["content"], "task-2")

    def test_grader_check_includes_solved_tasks_and_uses_quota_handoff(self):
        self.prepare_runner_fixture(("task-3",))
        self.write_run("first", self.run | {"selected_tasks": ["task-1", "task-2"]}, self.results)

        def openrouter_chat(model, messages, profile, seed):
            if messages[0]["content"] == "task-2" and seed == 2:
                body = b'{"error":{"metadata":{"limit_source":"openrouter_free_tier_daily"}}}'
                error = HTTPError("https://example.org", 429, "quota", {}, io.BytesIO(body))
                raise sweep.openrouter_api.RateLimited(error)
            return self.reply(model, messages, profile, seed, "#### 5")

        with patch.object(sweep.openrouter_api, "free_requests_remaining", return_value=1):
            with patch.object(sweep.openrouter_api, "chat", side_effect=openrouter_chat) as hosted:
                with patch.object(run.ollama_api, "chat", side_effect=self.reply) as local:
                    with redirect_stdout(io.StringIO()):
                        sweep.main(["fixture", "--verify-grader", "--ollama-model", MODEL["id"],
                                    "--ollama-profile", "default"])
        self.assertEqual([call.args[1][0]["content"] for call in hosted.call_args_list],
                         ["task-1", "task-1", "task-2", "task-2"])
        self.assertEqual([call.args[1][0]["content"] for call in local.call_args_list],
                         ["task-2", "task-2"])

        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        build_sqlite.build_database(db, include_local=True)
        results = db.execute("""
            SELECT m.provider, rt.task_key, rt.result FROM run_task rt
            JOIN run r ON r.benchmark_id = rt.benchmark_id AND r.id = rt.run_id
            JOIN model m ON m.id = r.model_id
            WHERE r.local = 1
        """)
        self.assertEqual({tuple(row) for row in results},
                         {("openrouter", "task-1", "fail"), ("openrouter", "task-2", "pending"),
                          ("ollama", "task-2", "pass")})

    def test_valid_run_loads_and_reports_task_status(self):
        db, errors = self.build()
        self.assertEqual(errors, [])
        self.assertEqual(db.execute("SELECT count(*) FROM model_call").fetchone()[0], 4)
        status = dict(db.execute("SELECT task_key, status FROM task_status").fetchall())
        self.assertEqual(status, {"task-1": "solved", "task-2": "open"})

    def test_sweep_reports_missing_evaluator_setup(self):
        self.prepare_runner_fixture()
        with (self.benchmark_dir / "eval.py").open("a") as evaluator:
            evaluator.write('\ndef setup_error():\n    return "install the fixture harness"\n')

        args = ["--dry-run", "--ollama-model", MODEL["id"], "--ollama-profile", "default"]
        error_output = io.StringIO()
        with redirect_stderr(error_output), self.assertRaises(SystemExit):
            sweep.main(args + ["fixture"])
        self.assertIn("cannot evaluate fixture (install the fixture harness)", error_output.getvalue())

        error_output = io.StringIO()
        output = io.StringIO()
        with redirect_stderr(error_output), redirect_stdout(output):
            sweep.main(args + ["--all"])
        self.assertIn("Skipping fixture (install the fixture harness)", error_output.getvalue())
        self.assertEqual(output.getvalue(), "")

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

    def test_stopped_run_may_be_partial(self):
        self.write_run("first", self.run | STOPPED, self.results[:1])
        db, errors = self.build()
        self.assertEqual(errors, [])
        self.assertEqual(db.execute("SELECT stop_reason FROM run").fetchone()[0], "Too slow.")

    def test_stopped_run_says_why(self):
        self.write_run("first", self.run | STOPPED | {"stop_reason": None}, self.results[:1])
        self.assertFails("CHECK constraint failed")

    def test_run_cannot_both_finish_and_stop(self):
        self.write_run("first", self.run | STOPPED | {"finished_at": "2026-11-19T01:00:00Z"}, self.results)
        self.assertFails("CHECK constraint failed")

    def test_stopped_run_cannot_end_in_a_partial_line(self):
        run_dir = self.write_run("first", self.run | STOPPED, self.results)
        with (run_dir / "results.jsonl").open("a") as f:
            f.write('{"key": "task-3", "res')
        with self.assertRaises(json.JSONDecodeError):
            self.build()

    def test_stop_keeps_finished_tasks_and_records_why(self):
        run_dir = self.write_run("first", self.run | {"finished_at": None}, self.results[::-1])
        with (run_dir / "results.jsonl").open("a") as f:
            f.write('{"key": "task-3", "res')
        argv = ["stop.py", "fixture", "first", "--reason", "Too slow."]
        with patch.object(stop, "ROOT", self.root), patch.object(sys, "argv", argv), \
                redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            stop.main()
        run = json.loads((run_dir / "run.json").read_text())
        self.assertEqual((run["finished_at"], run["stop_reason"]), (None, "Too slow."))
        keys = [json.loads(line)["key"] for line in (run_dir / "results.jsonl").read_text().splitlines()]
        self.assertEqual(keys, ["task-1", "task-2"])
        self.assertEqual(self.build()[1], [])

    def test_later_run_may_follow_a_stopped_run(self):
        self.write_run("first", self.run | STOPPED, self.results[:1])
        later = self.run | {"after_runs": ["first"], "started_at": "2026-11-19T02:00:00Z",
                            "finished_at": "2026-11-19T03:00:00Z"}
        self.write_run("second", later, self.results[1:])
        self.assertEqual(self.build()[1], [])

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
