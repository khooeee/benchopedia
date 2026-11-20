-- Explicit selections name the exact task keys. Older published runs select
-- all tasks their after_runs left open. Legacy local runs could use --limit.
WITH selected AS (
    SELECT r.benchmark_id, r.id AS run_id, requested.value AS task_key, r.finished_at
    FROM run r, json_each(r.selected_tasks) requested
    WHERE r.selected_tasks IS NOT NULL
    UNION ALL
    SELECT r.benchmark_id, r.id AS run_id, t.key AS task_key, r.finished_at
    FROM run r
    JOIN task t ON t.benchmark_id = r.benchmark_id
    WHERE r.selected_tasks IS NULL AND r.local = 0 AND NOT EXISTS (
        SELECT 1 FROM json_each(r.after_runs) earlier
        JOIN run_task p ON p.benchmark_id = r.benchmark_id AND p.run_id = earlier.value
                       AND p.task_key = t.key AND p.result = 'pass')
)
SELECT s.benchmark_id, s.run_id, s.task_key, 'unknown or repeated selection' AS problem
FROM selected s
LEFT JOIN task t ON t.benchmark_id = s.benchmark_id AND t.key = s.task_key
GROUP BY s.benchmark_id, s.run_id, s.task_key
HAVING count(*) > 1 OR count(t.key) = 0
UNION ALL
SELECT s.benchmark_id, s.run_id, s.task_key, 'missing from a finished run' AS problem
FROM selected s
WHERE s.finished_at IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM run_task rt
                  WHERE rt.benchmark_id = s.benchmark_id AND rt.run_id = s.run_id
                    AND rt.task_key = s.task_key AND rt.result <> 'pending')
UNION ALL
SELECT rt.benchmark_id, rt.run_id, rt.task_key, 'not selected by the run'
FROM run_task rt
JOIN run r ON r.benchmark_id = rt.benchmark_id AND r.id = rt.run_id
WHERE (r.selected_tasks IS NOT NULL OR r.local = 0)
  AND NOT EXISTS (SELECT 1 FROM selected s
                  WHERE s.benchmark_id = rt.benchmark_id AND s.run_id = rt.run_id
                    AND s.task_key = rt.task_key);
