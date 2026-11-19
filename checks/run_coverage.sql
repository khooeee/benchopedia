-- A run has results only for the tasks it selected: every task of its benchmark
-- that none of its after_runs passed. A finished run has a result for all of them.
WITH selected AS (
    SELECT r.benchmark_id, r.id AS run_id, t.key AS task_key, r.finished_at
    FROM run r
    JOIN task t ON t.benchmark_id = r.benchmark_id
    WHERE NOT EXISTS (
        SELECT 1 FROM json_each(r.after_runs) earlier
        JOIN run_task p ON p.benchmark_id = r.benchmark_id AND p.run_id = earlier.value
                       AND p.task_key = t.key AND p.result = 'pass')
)
SELECT s.benchmark_id, s.run_id, s.task_key, 'missing from a finished run' AS problem
FROM selected s
WHERE s.finished_at IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM run_task rt
                  WHERE rt.benchmark_id = s.benchmark_id AND rt.run_id = s.run_id
                    AND rt.task_key = s.task_key)
UNION ALL
SELECT rt.benchmark_id, rt.run_id, rt.task_key, 'not selected by the run'
FROM run_task rt
WHERE NOT EXISTS (SELECT 1 FROM selected s
                  WHERE s.benchmark_id = rt.benchmark_id AND s.run_id = rt.run_id
                    AND s.task_key = rt.task_key);
