# Running a sweep

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

An evaluator with local prerequisites can define `check_setup()`. It returns
`None` when setup is ready, or a message explaining how to fix the setup. The
sweep reports the message before making model calls for that benchmark.

## Run a repository-wide sweep

Start with `python3 runner/sweep.py --all --dry-run`. Check the scope and task
order, and record each skipped benchmark with its blocker. Run with `--all`
when the discovered evaluators support their protocols. If an evaluator is
present but lacks a capability its protocol requires, leave that benchmark out
and pass the eligible benchmark IDs explicitly.

A sweep is one pass through the eligible tasks. Complete at most one new
evaluation per task over that pass, including across restarts. Monitor the run
until the pass finishes, OpenRouter's daily quota runs out, the user asks you
to stop, or no eligible work can proceed.

Retry transient failures and resume an interrupted batch using its saved
command and checkpoints. Keep track of the run IDs and completed benchmark and
task pairs. The runner deduplicates within an invocation. If you restart the
sweep, use the saved results to exclude pairs already completed in this pass.
Use exact `--task-key` selections with `runner/run.py --scratch` when needed to
continue a saved queue. For a benchmark-specific blocker, preserve its work,
record the blocker, and continue the other benchmarks in priority order. If a
blocker prevents further progress, report what would let the sweep resume.

Keep results and checkpoints in scratch runs. At the end, rebuild the local
preview with `python3 scripts/build_site.py --local-runs` and report why the
sweep stopped, which benchmarks it covered, completed evaluations, new verified
solves, remaining open or pending tasks, and skipped benchmarks with their
reasons. Include the run IDs and the `build/local-site/` preview path.

For a goal that also includes adding benchmarks, finish the sweep report when
quota runs out or the pass completes, then continue with the
[benchmark addition workflow](adding-a-benchmark.md#add-benchmarks-continuously).

## Task and model priorities

Evaluate eligible untested tasks first, then pending tasks, then open tasks
with a completed failed evaluation. Every required attempt must be correct to pass.
A wrong or unparseable reply counts as a failed attempt. A recorded
evaluation stays pending while the required attempts or grading are
incomplete. A task stays retired once it has a verified solve for the
imported revision. Among open tasks, the sweep prioritizes those that have yet
to face the configured model and profile.
For benchmarks with numeric metrics, a task is **scored** once all its attempts
have valid scores. A regular sweep then moves on. The local preview shows
per-attempt scores and the mean over scored tasks in the run.

OpenRouter is the only provider for new runs. Sweeps and grader checks use
NVIDIA Nemotron 3 Ultra `:free`. Copy `.env.template` to `.env` and set
`OPENROUTER_API_KEY` there or in the process environment.
`make openrouter-quota` reports the daily allowance remaining. The sweep ends
when the daily quota is exhausted. If quota runs out during a batch, the
completed results and partial calls stay in the scratch run. Resume that run
using its recorded command when quota is available again.

`build/` is not committed, so those files disappear with the machine. Before
leaving an interrupted sweep, copy its runs into the repository:

```sh
python3 runner/checkpoint.py
```

That writes `sweep-runs/<benchmark>/<run-id>/`, including `results.jsonl` and
any `partial/` calls. Commit that directory. A later `runner/sweep.py` or the
recorded resume command copies a missing scratch run back from `sweep-runs/`
before it calls the model, so committed evaluations are not repeated.

## Verify a grader

Use `--verify-grader` with one benchmark when adding or changing its evaluator.
The sweep checks up to two tasks in task-key order, including previously solved
tasks. Set `--limit` to change the sample size.

```sh
python3 runner/sweep.py gsm8k --verify-grader
```

## Resume a recorded run

The run's `run.json` records the exact task keys and the command to resume with
the same run ID. Resuming requires the original runner, grader, model
configuration, and settings captured by the run.

Local runs live in `build/scratch-runs/<benchmark>/<run-id>/`. Each completed
task has one line in `results.jsonl` with its grades and raw model exchanges.
The `partial/` directory saves returned calls for unfinished tasks so they
can be graded or resumed. Committed copies of sweep runs live in
`sweep-runs/` and are restored into `build/scratch-runs/` when the scratch
copy is missing. Historical published results live in
`data/<benchmark>/runs/<run-id>/`, with their original model metadata and code
snapshots.

## Browse the evidence

The **Open tasks** page shows tasks with a completed failed evaluation and
zero verified solves. It includes evaluated coverage and links to each task's
recorded attempts. Task pages show first-solve attribution and run history.

The local lookup uses published results plus local runs whose task revision
and captured grader match the catalog. Build a local preview of that evidence
with `python3 scripts/build_site.py --local-runs`. Serve `build/local-site/`
locally. The standard build in `dist/` uses committed published results.
