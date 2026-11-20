# Future goals

## Find benchmark tasks that models have yet to solve

Build a catalog-wide **Open tasks** page that answers which questions still
have zero verified solves after the models Benchopedia has tried. Each row
should link to the task, show which models and profiles tried it, and link to
their grades and trajectories. Add a benchmark filter and show how far each
task has progressed through the configured model sequence.

An open task has at least one valid scored failure and zero verified solves
for its task revision. Show untested coverage alongside open and solved
counts. Give incomplete runs, execution errors, and unparseable replies a
visible place in the run history so readers can interpret the evidence.

## Evaluation workflow

1. **Grow the catalog.** Import redistributable benchmark snapshots and track
   evaluation readiness as graders and environments become available.
   [Adding a benchmark](adding-a-benchmark.md)
2. **Define what counts as a solve.** Use the benchmark's scoring rule at the
   task level. Retire a task after its first verified solve, with repeated
   confirmation where guessing makes a single correct answer weak evidence.
   Preserve raw scores for benchmarks that report graded metrics and define
   a pass criterion where the metric supports one.
3. **Prioritize first attempts.** Within the scope of a requested run, work
   through every eligible task awaiting its first attempt before retrying
   tasks with a valid wrong grade and zero verified solves.
4. **Use the OpenRouter quota first.** Start each benchmark sweep with the
   configured `nvidia/nemotron-3-ultra-550b-a55b:free` model. When the daily
   quota runs out, continue the pending queue on Ollama, including tasks
   awaiting their first attempt. Pace requests within OpenRouter's per-minute
   limit. Start a separate run when switching models and retain any completed
   OpenRouter attempts.
   [Nemotron model configuration](../runner/models/nemotron-3-ultra-550b-a55b-free.json)
5. **Escalate scored failures.** Schedule tasks that received a valid wrong
   grade on a stronger model as part of the benchmark's evaluation sequence.
   Use the full set of prior run IDs with the current `--after` implementation
   so tasks solved at any earlier stage stay retired. Keep interrupted or
   ungraded work eligible for completion.
   [Task selection](../runner/run.py#L117)
6. **Keep the full history.** Save model calls as they return and verdicts as
   they become available. Record the task revision, grader version, model,
   provider, settings, requests, responses, and tool actions where applicable.
   Keep first-solve attribution and all earlier trajectories available from
   the task page. As result volume grows, keep the full trajectory archive
   durable and use a smaller index for browsing.

## Implementation order

1. Agree on the solve criteria and the evidence that qualifies a task for the
   Open tasks page. Reuse the existing task-status view and trajectory records
   as the starting point.
   [Task status and run schema](../db/schema.sql#L114)
2. After approval, validate the quota handoff on one benchmark with an
   existing grader. Confirm that the daily limit triggers Ollama to take the
   next pending task in the same priority order, that solved tasks stay
   retired, and that results from both providers retain model attribution.
3. Build the catalog-wide page from the validated result index. Show both the
   number of open tasks and the number of tasks actually evaluated.
4. Expand grader coverage and automate model stages with explicit request and
   budget limits.
