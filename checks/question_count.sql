-- Every benchmark has exactly as many questions loaded as it declares.
SELECT b.id, b.question_count AS declared, count(q.key) AS loaded
FROM benchmark b
LEFT JOIN question q ON q.benchmark_id = b.id
GROUP BY b.id
HAVING declared <> loaded;
