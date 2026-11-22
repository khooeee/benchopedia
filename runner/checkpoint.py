"""Copy sweep scratch runs into git and restore them after a fresh checkout.

    python3 runner/checkpoint.py

Copies every build/scratch-runs/<benchmark>/sweep-openrouter-*/ directory into
sweep-runs/, which is committed. An interrupted run's results.jsonl and partial/
calls are included. Pass benchmark/run-id pairs to copy only those runs.

runner/sweep.py restores a missing scratch directory from sweep-runs/ before it
chooses tasks, so a new machine does not repeat committed evaluations. Resuming
the command in run.json restores that run first.
"""

import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRATCH = ROOT / "build" / "scratch-runs"
SAVED = ROOT / "sweep-runs"


def sweep_run_dirs(root=ROOT):
    scratch = root / "build" / "scratch-runs"
    if not scratch.is_dir():
        return []
    return sorted(
        path.parent for path in scratch.glob("*/*/run.json")
        if path.parent.name.startswith("sweep-openrouter-")
    )


def checkpoint_runs(directories, root=ROOT):
    """Replace each saved copy with the current scratch directory."""
    saved_root = root / "sweep-runs"
    copied = []
    for directory in directories:
        directory = Path(directory)
        if not (directory / "run.json").is_file():
            raise SystemExit(f"{directory} has no run.json")
        try:
            benchmark, run_id = directory.relative_to(root / "build" / "scratch-runs").parts
        except ValueError:
            raise SystemExit(f"{directory} is not a scratch run") from None
        if benchmark != Path(benchmark).name or run_id != Path(run_id).name:
            raise SystemExit(f"{directory} is not a single scratch run")
        target = saved_root / benchmark / run_id
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(directory, target)
        copied.append(target)
    return copied


def restore_run(benchmark, run_id, root=ROOT):
    """Copy one committed run into scratch when the scratch copy is absent."""
    source = root / "sweep-runs" / benchmark / run_id
    dest = root / "build" / "scratch-runs" / benchmark / run_id
    if (dest / "run.json").is_file() or not (source / "run.json").is_file():
        return False
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, dest)
    return True


def restore_sweep_runs(root=ROOT):
    saved = root / "sweep-runs"
    if not saved.is_dir():
        return 0
    restored = 0
    for run_json in sorted(saved.glob("*/*/run.json")):
        if restore_run(run_json.parent.parent.name, run_json.parent.name, root):
            restored += 1
    return restored


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args:
        directories = [ROOT / "build" / "scratch-runs" / arg for arg in args]
    else:
        directories = sweep_run_dirs()
    if not directories:
        raise SystemExit("No sweep scratch runs to commit.")
    for target in checkpoint_runs(directories):
        print(target.relative_to(ROOT))


if __name__ == "__main__":
    main()
