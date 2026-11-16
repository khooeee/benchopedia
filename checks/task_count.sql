-- Every benchmark has exactly as many tasks loaded as it declares.
SELECT b.id, b.task_count AS declared, count(q.key) AS loaded
FROM benchmark b
LEFT JOIN task q ON q.benchmark_id = b.id
GROUP BY b.id
HAVING declared <> loaded;
