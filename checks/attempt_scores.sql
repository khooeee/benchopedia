-- Metric names must be present and their values must be numbers.
SELECT a.benchmark_id, a.run_id, a.task_key, a.number
FROM attempt a
WHERE a.scores IS NOT NULL AND (
    NOT EXISTS (SELECT 1 FROM json_each(a.scores))
    OR EXISTS (SELECT 1 FROM json_each(a.scores) WHERE trim(key) = '' OR type NOT IN ('integer', 'real'))
);
