# Running benchmarks

Use the sweep runner for benchmark evaluations and grader checks. It can cover
one benchmark, a list of benchmarks, or all eligible benchmarks. The work list
comes from imported tasks and the SQLite `task_status` view.

```sh
python3 runner/sweep.py gsm8k boolq --dry-run --limit 10
python3 runner/sweep.py gsm8k boolq --limit 10
```

Pass `--all` to include every benchmark with imported tasks and a sweep
evaluator. It reports imported benchmarks it skips because they lack an
evaluator. If you name an unavailable benchmark explicitly, the sweep stops
before making any model calls. `--limit` caps task evaluations, and each
evaluation can require multiple model calls. The dry run lists candidate tasks
using the OpenRouter profile's priority order.

Use existing evaluators for sweep requests. Adding or changing an evaluator
is a separate task. Before starting a sweep, check that the evaluator and runner
support the benchmark's evaluation protocol in its `how-to-run.md`. If the
evaluator or a required harness, tool loop, or grading capability is missing,
report the benchmark and the specific blocker. For example, Terminal-Bench 2.0
is blocked until the sweep can run an agent in Harbor and record the verifier's
result.

## Task and model priorities

Evaluate eligible tasks awaiting a first attempt before tasks with a
completed failed evaluation. Every required attempt must be correct to pass.
A wrong or unparseable reply counts as a failed attempt. A recorded
evaluation stays pending while the required attempts or grading are
incomplete. A task stays retired once it has a verified solve for the
imported revision. For retries, prefer an available model the task has yet to face.

Sweeps and grader checks start with NVIDIA Nemotron 3 Ultra `:free` on
OpenRouter. Copy `.env.template` to `.env` and set `OPENROUTER_API_KEY` there
or in the process environment.
`make openrouter-quota` reports the daily allowance remaining. When OpenRouter
reports that the daily quota is exhausted, the sweep refreshes task status
from the saved results and starts an Ollama run with the next eligible tasks.
The Ollama defaults are `qwen3.6-35b-a3b` and its `scratch` profile. Set
`--ollama-model` and `--ollama-profile` to use another local configuration.

## Verify a grader

Use `--verify-grader` with one benchmark when adding or changing its evaluator.
The sweep checks up to two tasks in task-key order, including previously solved
tasks. Set `--limit` to change the sample size.

```sh
python3 runner/sweep.py gsm8k --verify-grader
```

## Resume a recorded run

The run's `run.json` records the exact task keys and the command to resume with
the same run ID and provider.

Local runs live in `build/scratch-runs/<benchmark>/<run-id>/`. Each completed
task has one line in `results.jsonl` with its grades and raw model exchanges.
The `partial/` directory saves returned calls for unfinished tasks so they
can be graded or resumed. Each provider gets its own run record. Historical
published results live in `data/<benchmark>/runs/<run-id>/`.

## Browse the evidence

The **Open tasks** page shows tasks with a completed failed evaluation and
zero verified solves. It includes evaluated coverage and links to each task's
recorded attempts. Task pages show first-solve attribution and run history.

The local lookup uses published results plus local runs whose task revision
and captured grader match the catalog. Build a local preview of that evidence
with `python3 scripts/build_site.py --local-runs`. Serve `build/local-site/`
locally. The standard build in `dist/` uses committed published results.
