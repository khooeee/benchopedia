-- Native score values must respect each metric's documented bounds.
SELECT s.id, s.value, m.id AS metric_id, m.min_value, m.max_value
FROM score s
JOIN evaluation_setup e ON e.id = s.setup_id
JOIN benchmark_metric m ON m.id = e.metric_id
WHERE (m.min_value IS NOT NULL AND s.value < m.min_value)
   OR (m.max_value IS NOT NULL AND s.value > m.max_value);
