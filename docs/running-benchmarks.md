# Running benchmarks

Use the sweep runner when asked to evaluate a benchmark or several benchmarks.
It selects tasks with an imported snapshot and a benchmark grader, and uses
the SQLite `task_status` view as its work list.

```sh
python3 runner/sweep.py gsm8k boolq --dry-run --limit 10
python3 runner/sweep.py gsm8k boolq --limit 10
```

Pass `--all` to include every benchmark with a grader. `--limit` caps task
evaluations, and each evaluation can require multiple model calls. The
dry run lists candidate tasks using the OpenRouter profile's priority order.

## Task and model priorities

Evaluate eligible tasks awaiting a first attempt before tasks with a
completed failed evaluation. Every required attempt must be correct to pass.
A wrong or unparseable reply counts as a failed attempt. A recorded
evaluation stays pending while the required attempts or grading are
incomplete. A task stays retired once it has a verified solve for the
imported revision. For retries, prefer an available model the task has yet to face.

The sweep starts with NVIDIA Nemotron 3 Ultra `:free` on OpenRouter. Copy
`.env.template` to `.env` and set `OPENROUTER_API_KEY` to use it.
`make openrouter-quota` reports the daily allowance remaining. When OpenRouter
reports that the daily quota is exhausted, the sweep refreshes task status
from the saved results and starts an Ollama run with the next eligible tasks.
The Ollama defaults are `qwen3.6-35b-a3b` and its `scratch` profile. Set
`--ollama-model` and `--ollama-profile` to use another local configuration.

## Exact selections and resume

For a particular list of tasks, repeat `--task-key` in the desired order.
The runner records that selection in `run.json`. Repeat the same command
and run ID to resume an interrupted run.

```sh
python3 runner/run.py gsm8k --scratch --run-id example-pair \
    --model qwen3.6-35b-a3b --profile scratch \
    --task-key test-0001 --task-key test-0003
```

Local runs live in `build/scratch-runs/<benchmark>/<run-id>/`. Each completed
task has one line in `results.jsonl` with its grades and raw model exchanges.
The `partial/` directory saves returned calls for unfinished tasks so they
can be graded or resumed. Each provider gets its own run record. Published
runs live in `data/<benchmark>/runs/<run-id>/`.

## Browse the evidence

The **Open tasks** page shows tasks with a completed failed evaluation and
zero verified solves. It includes evaluated coverage and links to each task's
recorded attempts. Task pages show first-solve attribution and run history.

The local lookup uses published results plus local runs whose task revision
and captured grader match the catalog. Build a local preview of that evidence
with `python3 scripts/build_site.py --local-runs`. Serve `build/local-site/`
locally. The standard build in `dist/` uses committed published results.
