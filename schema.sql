-- The database is rebuilt from data/ on every build, so there are no migrations:
-- change this file, rebuild, and the constraints are re-checked against all data.

CREATE TABLE benchmark (
    id               TEXT PRIMARY KEY CHECK (id <> '' AND id NOT GLOB '*[^a-z0-9-]*'),
    name             TEXT NOT NULL UNIQUE CHECK (trim(name) <> ''),
    summary          TEXT NOT NULL CHECK (trim(summary) <> ''),
    homepage_url     TEXT NOT NULL CHECK (homepage_url LIKE 'https://%'),
    dataset_url      TEXT NOT NULL CHECK (dataset_url LIKE 'https://%'),
    -- Upstream revision that data/<id>/questions.jsonl was imported from.
    dataset_revision TEXT NOT NULL CHECK (trim(dataset_revision) <> ''),
    released_on      TEXT NOT NULL CHECK (released_on = date(released_on)),
    -- Declared size; checks/question_count.sql compares it to the rows actually loaded.
    question_count   INTEGER NOT NULL CHECK (question_count > 0)
) STRICT;

CREATE TABLE question (
    benchmark_id TEXT NOT NULL REFERENCES benchmark (id),
    -- The benchmark's own identifier for the question.
    key          TEXT NOT NULL CHECK (key <> '' AND key = trim(key)),
    -- What the model is given.
    prompt       TEXT NOT NULL CHECK (trim(prompt) <> ''),
    source_url   TEXT CHECK (source_url LIKE 'https://%'),
    PRIMARY KEY (benchmark_id, key)
) STRICT;

-- Optional editorial content for the benchmark's encyclopedia page.
CREATE TABLE benchmark_article (
    benchmark_id TEXT PRIMARY KEY REFERENCES benchmark (id),
    category     TEXT NOT NULL CHECK (trim(category) <> ''),
    task         TEXT NOT NULL CHECK (trim(task) <> ''),
    metric       TEXT NOT NULL CHECK (trim(metric) <> ''),
    language     TEXT NOT NULL CHECK (trim(language) <> ''),
    overview     TEXT NOT NULL CHECK (trim(overview) <> ''),
    methodology  TEXT NOT NULL CHECK (trim(methodology) <> ''),
    scoring      TEXT NOT NULL CHECK (trim(scoring) <> ''),
    limitations  TEXT NOT NULL CHECK (trim(limitations) <> ''),
    sources      TEXT NOT NULL CHECK (json_valid(sources) AND json_type(sources) = 'array'
                                     AND json_array_length(sources) > 0)
) STRICT;
