-- The weights a run reported using are the weights its model definition pins.
SELECT r.benchmark_id, r.id AS run_id, m.weights_digest AS pinned,
       json_extract(r.environment, '$.weights_digest') AS reported
FROM run r
JOIN model m ON m.id = r.model_id
WHERE json_extract(r.environment, '$.weights_digest') IS NOT m.weights_digest;
