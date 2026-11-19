-- A task passes a run exactly when it made every attempt the run requires,
-- numbered from 1, and all of them passed.
SELECT rt.benchmark_id, rt.run_id, rt.task_key, rt.result,
       r.attempts_per_task AS required, count(a.number) AS attempts,
       max(a.number) AS last_attempt, total(a.verdict = 'pass') AS passed
FROM run_task rt
JOIN run r ON r.benchmark_id = rt.benchmark_id AND r.id = rt.run_id
LEFT JOIN attempt a
       ON a.benchmark_id = rt.benchmark_id AND a.run_id = rt.run_id AND a.task_key = rt.task_key
GROUP BY rt.benchmark_id, rt.run_id, rt.task_key
HAVING attempts <> required
    OR last_attempt <> required
    OR (rt.result = 'pass') <> (passed = required);
