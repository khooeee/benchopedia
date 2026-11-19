-- License and copyright details belong in data/<id>/redistribution-review.md,
-- not in the article sections or how-to-run guide.
SELECT id, section
FROM (
    SELECT id, 'overview' AS section, overview AS text FROM benchmark
    UNION ALL SELECT id, 'methodology', methodology FROM benchmark
    UNION ALL SELECT id, 'scoring', scoring FROM benchmark
    UNION ALL SELECT id, 'limitations', limitations FROM benchmark
    UNION ALL SELECT id, 'how_to_run', how_to_run FROM benchmark
)
WHERE text LIKE '%licen%' OR text LIKE '%copyright%';
