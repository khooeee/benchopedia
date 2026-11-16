"""Offline checks for complete imports, source preservation, and failure safety."""

import importlib.util
import io
import json
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("bbeh_import", Path(__file__).with_name("import.py"))
IMPORTER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(IMPORTER)
REVISION = "80d12ca916b7158f22293fcf3144f4d3d854d4be"


def full_release():
    return {
        group: {"examples": [{"input": f"{group} example {index}", "target": "0"}
                             for index in range(count)], "canary": IMPORTER.CANARY}
        for group, count in IMPORTER.EXPECTED_COUNTS.items()
    }


def archive_bytes(groups, duplicate=None, directory="benchmark_tasks"):
    out = io.BytesIO()
    with tarfile.open(fileobj=out, mode="w:gz") as archive:
        entries = list(groups.items())
        if duplicate:
            entries.append((duplicate, groups[duplicate]))
        for group, data in entries:
            content = json.dumps(data, ensure_ascii=False).encode("utf-8")
            member = tarfile.TarInfo(f"bbeh-{REVISION}/bbeh/{directory}/{group}/task.json")
            member.size = len(content)
            archive.addfile(member, io.BytesIO(content))
    return out.getvalue()


class ImportTests(unittest.TestCase):
    def test_full_release_preserves_text_positions_duplicates_and_source_pin(self):
        groups = full_release()
        prompt = "  table | <svg> & λ\nA | B\u2028C\u2029D\n\n"
        groups["bbeh_linguini"]["examples"][0] = {"input": prompt, "target": "\n  answer λ\n"}
        groups["bbeh_linguini"]["examples"][1] = {"input": prompt, "target": "different"}
        tasks = IMPORTER.convert_archive(archive_bytes(groups), REVISION)
        self.assertEqual(len(tasks), 4520)
        self.assertEqual(len({task["key"] for task in tasks}), 4520)
        self.assertEqual(tasks, sorted(tasks, key=lambda task: task["key"]))
        by_key = {task["key"]: task for task in tasks}
        self.assertEqual(by_key["linguini-001"]["prompt"], prompt)
        self.assertEqual(by_key["linguini-001"]["solution"], "\n  answer λ\n")
        self.assertEqual(by_key["linguini-002"]["prompt"], prompt)
        self.assertIn(f"/blob/{REVISION}/bbeh/benchmark_tasks/bbeh_linguini/task.json",
                      by_key["linguini-001"]["prompt_source_url"])
        self.assertEqual(sum(task["key"].startswith("disambiguation-qa-") for task in tasks), 120)

    def test_rejects_missing_and_unexpected_groups(self):
        for unknown in (False, True):
            groups = full_release()
            value = groups.pop("bbeh_nycc")
            if unknown:
                groups["unrecognized"] = value
            with self.subTest(unknown=unknown), self.assertRaises(ValueError):
                IMPORTER.convert_archive(archive_bytes(groups), REVISION)

    def test_rejects_truncated_group_and_mini_only_archive(self):
        groups = full_release()
        groups["bbeh_boardgame_qa"]["examples"].pop()
        with self.assertRaises(ValueError):
            IMPORTER.convert_archive(archive_bytes(groups), REVISION)
        with self.assertRaises(ValueError):
            IMPORTER.convert_archive(archive_bytes(full_release(), directory="mini"), REVISION)

    def test_rejects_duplicate_task_file_and_changed_canary(self):
        groups = full_release()
        with self.assertRaises(ValueError):
            IMPORTER.convert_archive(archive_bytes(groups, duplicate="bbeh_nycc"), REVISION)
        groups["bbeh_nycc"]["canary"] = "changed"
        with self.assertRaises(ValueError):
            IMPORTER.convert_archive(archive_bytes(groups), REVISION)

    def test_rejects_missing_empty_and_nontext_inputs_or_targets(self):
        for field in ("input", "target"):
            for bad in (None, "", "   ", 0):
                groups = full_release()
                groups["bbeh_nycc"]["examples"][0][field] = bad
                with self.subTest(field=field, value=bad), self.assertRaises(ValueError):
                    IMPORTER.convert_archive(archive_bytes(groups), REVISION)

    def test_failed_import_preserves_previous_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "benchmark.json").write_text(json.dumps({
                "dataset_revision": REVISION, "task_count": 4520,
            }))
            snapshot = root / "tasks.jsonl"
            snapshot.write_text("previous snapshot\n")
            with patch.object(IMPORTER, "BENCHMARK_DIR", root), patch.object(
                IMPORTER, "fetch_archive", return_value=archive_bytes({})
            ), self.assertRaises(ValueError):
                IMPORTER.main()
            self.assertEqual(snapshot.read_text(), "previous snapshot\n")
            self.assertFalse(snapshot.with_suffix(".jsonl.tmp").exists())

    def test_rejects_mutable_revision_and_partial_scope_before_fetching(self):
        for revision, count in (("main", 4520), (REVISION, 460)):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                (root / "benchmark.json").write_text(json.dumps({
                    "dataset_revision": revision, "task_count": count,
                }))
                with patch.object(IMPORTER, "BENCHMARK_DIR", root), patch.object(
                    IMPORTER, "fetch_archive"
                ) as fetch, self.assertRaises(SystemExit):
                    IMPORTER.main()
                fetch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
