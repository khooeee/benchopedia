-- Every run keeps a copy of its benchmark's eval.py and of its model definition.
SELECT r.benchmark_id, r.id AS run_id, needed.path AS missing_file
FROM run r
JOIN (SELECT benchmark_id, id, 'data/' || benchmark_id || '/eval.py' AS path FROM run
      UNION ALL
      SELECT benchmark_id, id, 'models/' || model_id || '.json' FROM run) needed
  ON needed.benchmark_id = r.benchmark_id AND needed.id = r.id
WHERE NOT EXISTS (SELECT 1 FROM run_file f
                  WHERE f.benchmark_id = r.benchmark_id AND f.run_id = r.id
                    AND f.path = needed.path);
