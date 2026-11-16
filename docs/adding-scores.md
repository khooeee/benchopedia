# Adding sourced scores

Store reviewed model results in an optional `data/<benchmark>/scores.json`.
The SQLite build loads this file after the benchmark and tasks, without network
access. Existing benchmarks need no score file. This adds storage and validation;
the website does not display these results yet.

Each snapshot has exactly three arrays, loaded in dependency order: `metrics`,
`setups`, and `scores`. Empty arrays are allowed. IDs are globally unique within
each table; prefix them with the benchmark ID. Relationships must stay within
the containing benchmark directory. The loader supplies each metric's
`benchmark_id`; do not include it in the file.

## Example format

This is a fictional example for the existing benchmark `example`, not a real
performance claim. Replace every record and source before adding production data.

```json
{
  "metrics": [
    {
      "id": "example-resolved",
      "name": "Resolved",
      "unit": "percent",
      "min_value": 0,
      "max_value": 100,
      "higher_is_better": true
    }
  ],
  "setups": [
    {
      "id": "example-standard-v1",
      "metric_id": "example-resolved",
      "dataset_revision": "immutable-dataset-revision",
      "split": "test",
      "agent": "Example Agent",
      "configuration": {
        "agent_version": "immutable-agent-revision",
        "tools": ["shell"],
        "attempt_policy": "one attempt per task",
        "budget": null
      },
      "documentation_url": "https://example.org/protocol"
    }
  ],
  "scores": [
    {
      "id": "example-run-1",
      "setup_id": "example-standard-v1",
      "model_name": "Fictional Model (version 1)",
      "value": 72.4,
      "reported_on": "2026-11-01",
      "observed_on": "2026-11-15",
      "source_url": "https://example.org/results#run-1",
      "source_revision": "immutable-result-revision-or-sha256"
    }
  ]
}
```

## Metrics and evaluation setups

Use a metric's native scale: `72.4` means 72.4 percent when its unit is `percent`.
Do not convert it to `0.724` or combine metrics with different units. Names and
units must be nonempty. Bounds may be omitted or `null` when undocumented or
unbounded; otherwise they must be finite numbers, with minimum below maximum.
`higher_is_better` is a required JSON boolean, not an integer.

A setup references one metric and documents the evaluated dataset revision,
split, agent, and configuration. Include agent versions, tools, attempt policy,
budgets, and any other settings that affect interpretation. `configuration` is
a JSON object; its keys are specific to the evaluation protocol. Keep unknown
settings explicit as `null`; optional dataset revision, split, and agent fields
may also be omitted or `null`. Empty strings are invalid. Link the official
protocol in `documentation_url` using an absolute HTTPS URL.

Create a new setup ID when a dataset revision, split, agent version, tools,
budget, or attempt policy changes. Do not assume two evaluations are comparable
because their unknown settings match, or infer a dataset revision from
Benchopedia's task snapshot. An incompletely documented setup preserves a
reported result without establishing a controlled comparison.

## Results and provenance

Use official leaderboard records, evaluation documentation, or primary reports.
Verify the exact benchmark variant, metric, model version, setup, and native
score value. Do not substitute an overall score for a subject score or mix
single-attempt results with best-of-many results.

Each score requires a stable run/record `id`, `setup_id`, `model_name`, finite
numeric `value`, `observed_on`, absolute HTTPS `source_url`, and nonempty
`source_revision`. Use a source permalink identifying the individual result
where available. Record an immutable commit, release, or content checksum in
`source_revision`; for checksum-based pins, retain the source snapshot and
reproduction instructions alongside the data. The loader checks that provenance
is present, not that a source exists or supports the claim.

`reported_on` is the source-supported reporting date, not a model's release date
or the evaluation's execution date. Omit it or use `null` when unknown.
`observed_on` records when the source was collected. Dates use real calendar dates
in `YYYY-MM-DD` format; reporting cannot follow collection. Never replace an
unknown reporting date with collection time or the first Git commit date.

Repeated evaluations of the same model and setup may have separate run IDs.
Keep an existing ID when observing the same upstream run again; do not append
another result just because the source was fetched again. Review corrections,
source revisions, and dates deliberately. Do not add fictional results or an
automatic network refresh to the build.

## Validation and derived values

Run from the repository root:

```sh
python3 scripts/check_scores.py
python3 scripts/helpers/build_sqlite.py
python3 scripts/build_site.py
python3 scripts/check_site.py
node scripts/check_ui.cjs
```

The schema enforces required fields, relationships, finite values, dates, and
metric definitions. The loader also checks JSON types, HTTPS URLs, unknown
fields, and benchmark ownership. `checks/score_bounds.sql` rejects results
outside their metric's bounds, inclusively. Errors identify the source file and
array record. Score checks use fictional fixtures, including rejected inputs
and an end-to-end database build. CI runs them before building the website.

Compute best scores within a documented comparable setup. For a higher-is-better
metric, the gap to the maximum is `max_value - best_value`; for a
lower-is-better metric it is `best_value - min_value`. An undocumented bound
means the gap is unknown. Percent gaps are percentage points. A gap is not a
saturation judgment, and scores from different setups must not share a frontier.
Best scores, gaps, and saturation labels are not stored in the database.
