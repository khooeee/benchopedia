"""Record that a run was ended early, and why.

    python3 runner/stop.py gsm8k example --scratch \\
        --reason "Stopped after 135 of 1,319 tasks because ..."

Stop the runner first (Ctrl-C, or kill its process). This drops a last line the
runner was still writing, sorts results.jsonl, and sets stopped_at and
stop_reason in run.json. The tasks the run reached keep their results; the site
shows the run as stopped, with the reason. A stopped run is not resumed: to try
the tasks it did not pass, start a new run with --after <run-id>.
"""

import argparse
import json

from run import ROOT, completed_keys, now, sort_results, write_json


def stop_run(run_dir, reason):
    run_file = run_dir / "run.json"
    run = json.loads(run_file.read_text(encoding="utf-8"))
    if run["finished_at"]:
        raise SystemExit(f"{run_file.parent} has already finished")
    if run.get("stopped_at"):
        raise SystemExit(f"{run_file.parent} was already stopped: {run['stop_reason']}")

    results_file = run_file.parent / "results.jsonl"
    completed_keys(results_file)
    records = sort_results(results_file)
    run |= {"stopped_at": now(), "stop_reason": reason}
    write_json(run_file, run)
    passed = sum(r["result"] == "pass" for r in records)
    scored = sum(r["result"] == "scored" for r in records)
    if scored:
        print(f"Stopped {run_file.parent}: {scored} of {len(records)} tasks scored")
    else:
        print(f"Stopped {run_file.parent}: {passed} of {len(records)} tasks passed")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("benchmark")
    parser.add_argument("run_id")
    parser.add_argument("--reason", required=True, help="why the run was stopped, for readers of its page")
    parser.add_argument("--scratch", action="store_true", help="stop a run in build/scratch-runs/")
    args = parser.parse_args()
    if not args.reason.strip():
        parser.error("--reason must say why the run was stopped")

    runs_dir = ROOT / "build" / "scratch-runs" / args.benchmark if args.scratch else ROOT / "data" / args.benchmark / "runs"
    stop_run(runs_dir / args.run_id, args.reason.strip())


if __name__ == "__main__":
    main()
