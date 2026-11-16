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
    -- data/<id>/redistribution-review.md, published as the page's License section.
    redistribution_review TEXT NOT NULL CHECK (trim(redistribution_review) <> ''),
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
