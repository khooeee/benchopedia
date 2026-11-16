-- License and copyright details belong in data/<id>/redistribution-review.md,
-- not in the article sections.
SELECT id, section
FROM (
    SELECT id, 'overview' AS section, overview AS text FROM benchmark
    UNION ALL SELECT id, 'methodology', methodology FROM benchmark
    UNION ALL SELECT id, 'scoring', scoring FROM benchmark
    UNION ALL SELECT id, 'limitations', limitations FROM benchmark
)
WHERE text LIKE '%licen%' OR text LIKE '%copyright%';
