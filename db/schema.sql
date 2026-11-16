-- The database is rebuilt from data/ on every build, so there are no migrations:
-- change this file, rebuild, and the constraints are re-checked against all data.

CREATE TABLE benchmark (
    id               TEXT PRIMARY KEY CHECK (id <> '' AND id NOT GLOB '*[^a-z0-9-]*'),
    name             TEXT NOT NULL UNIQUE CHECK (trim(name) <> ''),
    summary          TEXT NOT NULL CHECK (trim(summary) <> ''),
    homepage_url    TEXT NOT NULL CHECK (homepage_url LIKE 'https://%'),
    dataset_url      TEXT NOT NULL CHECK (dataset_url LIKE 'https://%'),
    -- Upstream revision that data/<id>/tasks.jsonl was imported from.
    dataset_revision TEXT NOT NULL CHECK (trim(dataset_revision) <> ''),
    released_on      TEXT NOT NULL CHECK (released_on = date(released_on)),
    -- Declared size; checks/task_count.sql compares it to the rows actually loaded.
    task_count       INTEGER NOT NULL CHECK (task_count > 0),
    -- Boolean: at least one imported task contains reference solution text.
    has_solutions    INTEGER NOT NULL CHECK (has_solutions IN (0, 1)),
    -- Article sections for the benchmark's encyclopedia page.
    overview         TEXT NOT NULL CHECK (trim(overview) <> ''),
    methodology      TEXT NOT NULL CHECK (trim(methodology) <> ''),
    scoring          TEXT NOT NULL CHECK (trim(scoring) <> ''),
    limitations      TEXT NOT NULL CHECK (trim(limitations) <> ''),
    sources          TEXT NOT NULL CHECK (json_valid(sources) AND json_type(sources) = 'array'
                                         AND json_array_length(sources) > 0)
) STRICT;

CREATE TABLE task (
    benchmark_id TEXT NOT NULL REFERENCES benchmark (id),
    -- The benchmark's own identifier for the task.
    key          TEXT NOT NULL CHECK (key <> '' AND key = trim(key)),
    -- What the model is given.
    prompt       TEXT NOT NULL CHECK (trim(prompt) <> ''),
    -- Reference solution supplied by the dataset, when available.
    solution     TEXT CHECK (trim(solution) <> ''),
    environment_url TEXT CHECK (environment_url LIKE 'https://%'),
    solution_source_url TEXT CHECK (solution_source_url LIKE 'https://%'),
    prompt_source_url   TEXT CHECK (prompt_source_url LIKE 'https://%'),
    PRIMARY KEY (benchmark_id, key)
) STRICT;

-- Scores use their metric's native scale (e.g. 72.4 percent, not 0.724).
CREATE TABLE benchmark_metric (
    id TEXT PRIMARY KEY CHECK (trim(id) <> ''),
    benchmark_id TEXT NOT NULL REFERENCES benchmark (id),
    name TEXT NOT NULL CHECK (trim(name) <> ''),
    unit TEXT NOT NULL CHECK (trim(unit) <> ''),
    -- NULL means the metric has no documented bound on this side.
    min_value REAL CHECK (abs(min_value) <= 1.7976931348623157e308),
    max_value REAL CHECK (abs(max_value) <= 1.7976931348623157e308),
    higher_is_better INTEGER NOT NULL CHECK (higher_is_better IN (0, 1)),
    CHECK (min_value IS NULL OR max_value IS NULL OR min_value < max_value)
) STRICT;

-- A change in dataset, agent version, tools, budget or attempt policy is a
-- different setup. Unknown settings must not imply comparable evaluations.
CREATE TABLE evaluation_setup (
    id TEXT PRIMARY KEY CHECK (trim(id) <> ''),
    metric_id TEXT NOT NULL REFERENCES benchmark_metric (id),
    dataset_revision TEXT CHECK (trim(dataset_revision) <> ''),
    split TEXT CHECK (trim(split) <> ''),
    agent TEXT CHECK (trim(agent) <> ''),
    configuration TEXT NOT NULL CHECK (json_valid(configuration)
                                      AND json_type(configuration) = 'object'),
    documentation_url TEXT NOT NULL CHECK (documentation_url LIKE 'https://_%')
) STRICT;

CREATE TABLE score (
    -- Stable upstream run/record identity, not a new ID for every scrape.
    id TEXT PRIMARY KEY CHECK (trim(id) <> ''),
    setup_id TEXT NOT NULL REFERENCES evaluation_setup (id),
    model_name TEXT NOT NULL CHECK (trim(model_name) <> ''),
    value REAL NOT NULL CHECK (abs(value) <= 1.7976931348623157e308),
    -- Reporting date is optional; collection date must never substitute for it.
    reported_on TEXT CHECK (reported_on IS NULL OR
        (length(reported_on) = 10 AND reported_on GLOB '????-??-??'
         AND date(reported_on, '+0 days') IS reported_on)),
    observed_on TEXT NOT NULL CHECK (
        length(observed_on) = 10 AND observed_on GLOB '????-??-??'
        AND date(observed_on, '+0 days') IS observed_on),
    source_url TEXT NOT NULL CHECK (source_url LIKE 'https://_%'),
    source_revision TEXT NOT NULL CHECK (trim(source_revision) <> ''),
    CHECK (reported_on IS NULL OR reported_on <= observed_on)
) STRICT;

CREATE INDEX metric_benchmark ON benchmark_metric (benchmark_id);
CREATE INDEX setup_metric ON evaluation_setup (metric_id);
CREATE INDEX score_setup ON score (setup_id);
