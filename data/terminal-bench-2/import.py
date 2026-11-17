"""Import all 89 Terminal-Bench 2.0 tasks from a pinned commit of the task repository.

Run from the repository root: python3 data/terminal-bench-2/import.py
Only Python's standard library is required. Imported scripts are never executed.
"""

import io
import json
import re
import sys
import tarfile
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "harbor-framework/terminal-bench-2"
EXPECTED_COUNT = 89
# Each task directory holds these files; other files are not imported.
INSTRUCTION = "instruction.md"
MANIFEST = "task.toml"
DOCKERFILE = "environment/Dockerfile"
ENTRY_POINT = "solution/solve.sh"


def fetch_files(revision):
    url = f"https://codeload.github.com/{REPOSITORY}/tar.gz/{revision}"
    with urllib.request.urlopen(url, timeout=300) as response:
        archive = response.read()
    files = {}
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        for member in tar.getmembers():
            # Strip the archive's top-level directory; read file contents in memory only.
            path = member.name.split("/", 1)[-1]
            if member.isfile() and re.fullmatch(r"[a-z0-9.-]+/solution/.+/.+", path):
                raise ValueError(f"{path}: nested solution files are not supported")
            if member.isfile() and re.fullmatch(r"[a-z0-9.-]+/(instruction\.md|task\.toml|"
                                                r"environment/Dockerfile|solution/[^/]+)", path):
                files[path] = tar.extractfile(member).read().decode("utf-8")
    return files


def manifest_value(task, manifest, field, pattern):
    values = re.findall(rf'^{field} = "({pattern})"$', manifest, re.M)
    if len(values) != 1:
        raise ValueError(f"{task}: expected one {field} in {MANIFEST}")
    return values[0]


def to_task(task, files, revision):
    instruction = files[f"{task}/{INSTRUCTION}"]
    if "~~~" in instruction or not instruction.endswith("\n") or not instruction.strip():
        raise ValueError(f"{task}: instruction cannot be fenced intact")
    manifest = files[f"{task}/{MANIFEST}"]
    category = manifest_value(task, manifest, "category", r"[a-z-]+")
    difficulty = manifest_value(task, manifest, "difficulty", r"easy|medium|hard")
    if f"{task}/{DOCKERFILE}" not in files:
        raise ValueError(f"{task}: missing {DOCKERFILE}")
    solution_files = sorted(path for path in files if path.startswith(f"{task}/solution/"))
    entry_point = f"{task}/{ENTRY_POINT}"
    if entry_point not in solution_files:
        raise ValueError(f"{task}: missing {ENTRY_POINT}")
    blob = f"https://github.com/{REPOSITORY}/blob/{revision}/{task}"
    if solution_files == [entry_point]:
        solution = files[entry_point]
        solution_source = f"{blob}/{ENTRY_POINT}"
    else:
        # Show the entry point first, then the files it uses, each under a header line.
        ordered = [entry_point] + [path for path in solution_files if path != entry_point]
        parts = []
        for path in ordered:
            text = files[path]
            parts.append(f"==> {path.split('/', 1)[1]} <==\n{text}" + ("" if text.endswith("\n") else "\n"))
        solution = "\n".join(parts)
        solution_source = f"https://github.com/{REPOSITORY}/tree/{revision}/{task}/solution"
    return {
        "key": task,
        "prompt": f"{task} ({category}, {difficulty})\n\n~~~markdown\n{instruction}~~~",
        "solution": solution,
        "prompt_source_url": f"{blob}/{INSTRUCTION}",
        "solution_source_url": solution_source,
        "environment_url": f"{blob}/{DOCKERFILE}",
    }


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 89 Terminal-Bench 2.0 tasks.")
    files = fetch_files(revision)
    task_names = sorted(path.split("/")[0] for path in files if path.endswith(f"/{INSTRUCTION}"))
    if len(task_names) != EXPECTED_COUNT:
        sys.exit(f"Expected {EXPECTED_COUNT} tasks, found {len(task_names)}.")
    tasks = [to_task(task, files, revision) for task in task_names]
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    print(f"Wrote {len(tasks):,} Terminal-Bench 2.0 tasks to {out}")


if __name__ == "__main__":
    main()
