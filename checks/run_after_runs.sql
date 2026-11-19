-- A run can only build on runs of the same benchmark that ended, finished or stopped, before it began.
SELECT r.benchmark_id, r.id AS run_id, earlier.value AS after_run
FROM run r, json_each(r.after_runs) earlier
LEFT JOIN run p ON p.benchmark_id = r.benchmark_id AND p.id = earlier.value
WHERE p.id IS NULL OR coalesce(p.finished_at, p.stopped_at) IS NULL
   OR coalesce(p.finished_at, p.stopped_at) > r.started_at;
