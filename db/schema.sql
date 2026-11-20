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
    -- This and has_solutions are NULL exactly when data/<id>/exclusions.md leaves
    -- the tasks out; the loader enforces that.
    task_count       INTEGER CHECK (task_count > 0),
    -- Boolean: at least one imported task contains reference solution text.
    has_solutions    INTEGER CHECK (has_solutions IN (0, 1)),
    -- Article sections for the benchmark's encyclopedia page.
    overview         TEXT NOT NULL CHECK (trim(overview) <> ''),
    methodology      TEXT NOT NULL CHECK (trim(methodology) <> ''),
    scoring          TEXT NOT NULL CHECK (trim(scoring) <> ''),
    limitations      TEXT NOT NULL CHECK (trim(limitations) <> ''),
    -- data/<id>/redistribution-review.md, published as the page's License section.
    redistribution_review TEXT NOT NULL CHECK (trim(redistribution_review) <> ''),
    -- data/<id>/how-to-run.md, the benchmark page's How to run section, where
    -- {{key}} stands for an example task's key. NULL exactly when the tasks are excluded.
    how_to_run       TEXT CHECK (instr(how_to_run, '{{key}}') > 0),
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

-- Runs: models attempting a benchmark's tasks. models/<id>.json defines a model;
-- data/<benchmark>/runs/<run>/ holds one run, written by runner/run.py.

-- A model as served. Ollama supplies a weights digest.
CREATE TABLE model (
    id             TEXT PRIMARY KEY CHECK (id <> '' AND id NOT GLOB '*[^a-z0-9.-]*'),
    name           TEXT NOT NULL CHECK (trim(name) <> ''),
    homepage_url   TEXT NOT NULL CHECK (homepage_url LIKE 'https://%'),
    provider       TEXT NOT NULL CHECK (provider IN ('ollama', 'openrouter')),
    provider_model TEXT NOT NULL CHECK (trim(provider_model) <> ''),
    weights_digest TEXT CHECK (weights_digest GLOB 'sha256:*'),
    CHECK ((weights_digest IS NOT NULL) = (provider = 'ollama'))
) STRICT;

-- One pass of one model over one benchmark's tasks, with fixed settings and code.
CREATE TABLE run (
    benchmark_id      TEXT NOT NULL REFERENCES benchmark (id),
    -- Its directory name under data/<benchmark>/runs/.
    id                TEXT NOT NULL CHECK (id <> '' AND id NOT GLOB '*[^a-z0-9.-]*'),
    model_id          TEXT NOT NULL REFERENCES model (id),
    -- The model profile the run used and the options it sent with every request.
    profile           TEXT NOT NULL CHECK (trim(profile) <> ''),
    settings          TEXT NOT NULL CHECK (json_valid(settings) AND json_type(settings) = 'object'),
    attempts_per_task INTEGER NOT NULL CHECK (attempts_per_task > 0),
    -- [] runs every task; otherwise only the tasks none of these earlier runs passed.
    after_runs        TEXT NOT NULL CHECK (json_valid(after_runs) AND json_type(after_runs) = 'array'),
    selected_tasks   TEXT CHECK (selected_tasks IS NULL OR
                                (json_valid(selected_tasks) AND json_type(selected_tasks) = 'array')),
    dataset_revision TEXT CHECK (trim(dataset_revision) <> ''),
    local             INTEGER NOT NULL DEFAULT 0 CHECK (local IN (0, 1)),
    model_file        TEXT,
    -- The Benchopedia commit the run's code and model definition came from.
    commit_sha        TEXT NOT NULL CHECK (length(commit_sha) = 40 AND commit_sha NOT GLOB '*[^0-9a-f]*'),
    -- Software and hardware versions, including the weights digest the provider reported.
    environment       TEXT NOT NULL CHECK (json_valid(environment) AND json_type(environment) = 'object'),
    started_at        TEXT NOT NULL CHECK (started_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T*Z'),
    -- Set once every selected task has a result; NULL while running or if the run was stopped.
    finished_at       TEXT CHECK (finished_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T*Z'
                                  AND finished_at >= started_at),
    -- Set when the run was ended early, with why; its results cover only the tasks it reached.
    stopped_at        TEXT CHECK (stopped_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T*Z'
                                  AND stopped_at >= started_at),
    stop_reason       TEXT CHECK (trim(stop_reason) <> ''),
    CHECK ((stopped_at IS NULL) = (stop_reason IS NULL)),
    CHECK (finished_at IS NULL OR stopped_at IS NULL),
    PRIMARY KEY (benchmark_id, id)
) STRICT;

-- The exact commands that produced the run, in order.
CREATE TABLE run_command (
    benchmark_id TEXT NOT NULL,
    run_id       TEXT NOT NULL,
    number       INTEGER NOT NULL CHECK (number > 0),
    command      TEXT NOT NULL CHECK (trim(command) <> ''),
    purpose      TEXT NOT NULL CHECK (trim(purpose) <> ''),
    PRIMARY KEY (benchmark_id, run_id, number),
    FOREIGN KEY (benchmark_id, run_id) REFERENCES run (benchmark_id, id)
) STRICT;

-- A copy of every file the runner read: its own code, the benchmark's eval.py
-- and the model definition, as they were when the run started.
CREATE TABLE run_file (
    benchmark_id TEXT NOT NULL,
    run_id       TEXT NOT NULL,
    path         TEXT NOT NULL CHECK (path <> '' AND path NOT LIKE '/%' AND path NOT LIKE '%..%'),
    content      TEXT NOT NULL,
    PRIMARY KEY (benchmark_id, run_id, path),
    FOREIGN KEY (benchmark_id, run_id) REFERENCES run (benchmark_id, id)
) STRICT;

-- One task in one run. A task passes only when every attempt passed, so a lucky
-- guess cannot pass it; checks/run_task_result.sql holds the two to each other.
CREATE TABLE run_task (
    benchmark_id TEXT NOT NULL,
    run_id       TEXT NOT NULL,
    task_key     TEXT NOT NULL,
    result       TEXT NOT NULL CHECK (result IN ('pass', 'fail', 'pending')),
    graded_at    TEXT CHECK (graded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T*Z'),
    PRIMARY KEY (benchmark_id, run_id, task_key),
    FOREIGN KEY (benchmark_id, run_id) REFERENCES run (benchmark_id, id),
    FOREIGN KEY (benchmark_id, task_key) REFERENCES task (benchmark_id, key)
) STRICT;

-- One try at a task. An unparseable answer fails the task like a wrong one, but
-- stays distinguishable so format failures are not mistaken for difficulty.
CREATE TABLE attempt (
    benchmark_id TEXT NOT NULL,
    run_id       TEXT NOT NULL,
    task_key     TEXT NOT NULL,
    number       INTEGER NOT NULL CHECK (number > 0),
    verdict      TEXT NOT NULL CHECK (verdict IN ('pass', 'fail', 'unparseable', 'pending')),
    -- The model's final text, which the grader read.
    output       TEXT NOT NULL,
    -- What the grader extracted from the output; NULL when it found nothing.
    answer       TEXT CHECK ((answer IS NULL) = (verdict IN ('unparseable', 'pending'))),
    started_at   TEXT NOT NULL CHECK (started_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T*Z'),
    PRIMARY KEY (benchmark_id, run_id, task_key, number),
    FOREIGN KEY (benchmark_id, run_id, task_key) REFERENCES run_task (benchmark_id, run_id, task_key)
) STRICT;

-- The trajectory: every request an attempt sent to the model and the response it
-- got back, exactly as exchanged, reasoning and token counts included.
CREATE TABLE model_call (
    benchmark_id   TEXT NOT NULL,
    run_id         TEXT NOT NULL,
    task_key       TEXT NOT NULL,
    attempt_number INTEGER NOT NULL,
    number         INTEGER NOT NULL CHECK (number > 0),
    request        TEXT NOT NULL CHECK (json_valid(request) AND json_type(request) = 'object'),
    response       TEXT NOT NULL CHECK (json_valid(response) AND json_type(response) = 'object'),
    latency_ms     INTEGER NOT NULL CHECK (latency_ms >= 0),
    PRIMARY KEY (benchmark_id, run_id, task_key, attempt_number, number),
    FOREIGN KEY (benchmark_id, run_id, task_key, attempt_number)
        REFERENCES attempt (benchmark_id, run_id, task_key, number)
) STRICT;

-- Count only evidence against the current dataset revision. Older published
-- records predate explicit revision tracking.
CREATE VIEW task_status AS
WITH evidence AS (
    SELECT rt.benchmark_id, rt.task_key, rt.result,
           rt.result = 'fail' AND EXISTS (
               SELECT 1 FROM attempt a
               WHERE a.benchmark_id = rt.benchmark_id AND a.run_id = rt.run_id
                 AND a.task_key = rt.task_key AND a.verdict = 'fail'
           ) AS wrong
    FROM run_task rt
    JOIN run r ON r.benchmark_id = rt.benchmark_id AND r.id = rt.run_id
    JOIN benchmark b ON b.id = rt.benchmark_id
    WHERE r.dataset_revision IS NULL OR r.dataset_revision = b.dataset_revision
)
SELECT t.benchmark_id, t.key AS task_key,
       CASE WHEN max(e.result = 'pass') THEN 'solved'
            WHEN max(e.wrong) THEN 'open'
            WHEN count(e.result) > 0 THEN 'pending'
            ELSE 'untested' END AS status,
       count(e.result) AS runs
FROM task t
LEFT JOIN evidence e ON e.benchmark_id = t.benchmark_id AND e.task_key = t.key
GROUP BY t.benchmark_id, t.key;
