-- Every attempt records at least one model call, numbered from 1 without gaps.
SELECT a.benchmark_id, a.run_id, a.task_key, a.number AS attempt,
       count(c.number) AS calls, max(c.number) AS last_call
FROM attempt a
LEFT JOIN model_call c
       ON c.benchmark_id = a.benchmark_id AND c.run_id = a.run_id
      AND c.task_key = a.task_key AND c.attempt_number = a.number
GROUP BY a.benchmark_id, a.run_id, a.task_key, a.number
HAVING calls = 0 OR last_call <> calls;
