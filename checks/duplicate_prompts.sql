-- No two questions in a benchmark share the same prompt.
SELECT benchmark_id, group_concat(key, ', ') AS keys
FROM question
GROUP BY benchmark_id, prompt
HAVING count(*) > 1;
