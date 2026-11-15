-- Every question has well-formed SWE-bench fields, and its key and source_url agree with its repo.
SELECT key, attrs ->> 'repo' AS repo, attrs ->> 'difficulty' AS difficulty, source_url
FROM question
WHERE benchmark_id = 'swe-bench-verified'
  AND NOT coalesce(
        attrs ->> 'repo' GLOB '?*/?*'
    AND key GLOB replace(attrs ->> 'repo', '/', '__') || '-[0-9]*'
    AND source_url = 'https://github.com/' || (attrs ->> 'repo') || '/pull/'
                     || substr(key, length(attrs ->> 'repo') + 3)
    AND length(attrs ->> 'base_commit') = 40
    AND attrs ->> 'base_commit' NOT GLOB '*[^0-9a-f]*'
    AND trim(attrs ->> 'version') <> ''
    AND attrs ->> 'created_at' = strftime('%Y-%m-%dT%H:%M:%SZ', attrs ->> 'created_at')
    AND attrs ->> 'difficulty' IN ('<15 min fix', '15 min - 1 hour', '1-4 hours', '>4 hours')
    AND json_type(attrs, '$.fail_to_pass') = 'array'
    AND json_array_length(attrs, '$.fail_to_pass') > 0
    AND json_type(attrs, '$.pass_to_pass_count') = 'integer',
    0);
