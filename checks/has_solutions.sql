-- Solution availability matches the imported task snapshot.
SELECT b.id, b.has_solutions AS declared,
       EXISTS (SELECT 1 FROM task q
               WHERE q.benchmark_id = b.id AND q.solution IS NOT NULL) AS loaded
FROM benchmark b
WHERE declared <> loaded;
