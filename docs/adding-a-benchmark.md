# Adding a benchmark

Add a benchmark by creating its metadata, tasks, and importer under `data/<id>/`.
The build discovers these directories automatically and generates the SQLite
database, benchmark page, task pages, and search index.

Use [SWE-bench Verified](../data/swe-bench-verified/) as a working example, and
[db/schema.sql](../db/schema.sql) as the authoritative field definitions. Adapt
the import to the new dataset; its identifiers, answers, and environment setup
may differ from SWE-bench's.

## 1. Choose the source and scope

Start with the official dataset, project documentation, paper, and evaluation
code. Establish:

- Which variant, version, configuration, and split to include, and its task count.
- The exact upstream revision: a commit, immutable release, or file checksum.
- What input a model receives, what it must produce, and how it is evaluated.
- Whether reference solutions and task environment instructions are available.
- Whether the task data can be redistributed under its license and access terms.

Write down the chosen scope in the benchmark page's methodology. For example,
importing only a test split should be explicit. Do not substitute a sample for
the complete declared split or silently skip records that are difficult to import.
If task inputs are unavailable or need a format the site cannot display, identify
that gap before treating the import as complete.

## 2. Create the benchmark directory

Choose a unique lowercase slug using letters, digits, and hyphens:

```text
data/example-benchmark/
    benchmark.json
    tasks.jsonl
    import.py
```

`benchmark.json` contains the metadata and explanatory text. `tasks.jsonl`
contains the imported task snapshot. `import.py` reproduces that snapshot from
the upstream source. Commit these files; `build/` and `dist/` are generated and
ignored by Git. Do not edit the generated database to add data.

## 3. Write benchmark.json

All fields below are required. This is a fictional two-task template; replace
every example value with information about the actual benchmark and real sources.

```json
{
  "id": "example-benchmark",
  "name": "Example Benchmark",
  "summary": "Two multiple-choice arithmetic tasks.",
  "homepage_url": "https://example.org/benchmark",
  "dataset_url": "https://example.org/dataset",
  "dataset_revision": "replace-with-an-immutable-upstream-revision",
  "released_on": "2026-01-01",
  "task_count": 2,
  "overview": "What the benchmark measures and why it exists.",
  "methodology": "Which version and split are included, the model inputs, and the evaluation procedure.",
  "scoring": "How outputs are graded and how the overall score is calculated.",
  "limitations": "Documented limitations and relevant comparison caveats.",
  "sources": [
    {"title": "Official dataset documentation", "url": "https://example.org/dataset"}
  ]
}
```

The `id` must match the directory name; `name` must be unique. `task_count` is
the number of tasks actually included in this snapshot. Use the release date of
the included benchmark variant in `YYYY-MM-DD` format.

The overview, methodology, scoring, and limitations are sections on the benchmark
page, not separate files. Write concise explanations supported by primary sources.
Use Markdown links near factual claims and list the sources in `sources` as well.
Do not invent performance results or conclusions about saturation.

These sections support basic Markdown: paragraphs, headings, links, and code
blocks. HTML is escaped. JSON strings represent newlines as `\n`.

## 4. Map upstream records to tasks.jsonl

Write one JSON object per line, encoded as UTF-8. The two records corresponding
to the fictional template above would be:

```jsonl
{"key":"arithmetic-001","prompt":"What is 2 + 2?\n\nA. 3\nB. 4\nC. 5","solution":"B. 4","prompt_source_url":"https://example.org/dataset/arithmetic-001"}
{"key":"arithmetic-002","prompt":"What is 3 + 3?\n\nA. 5\nB. 6\nC. 7","solution":"B. 6","prompt_source_url":"https://example.org/dataset/arithmetic-002"}
```

| Field | How to populate it |
| --- | --- |
| `key` | Required stable identifier, unique within this benchmark. Prefer the upstream ID. If none exists, document a deterministic identifier scheme. Include split or subject when needed to prevent collisions. |
| `prompt` | Required task text, including necessary context, instructions, and answer choices. Preserve the original wording and whitespace of imported text fields. |
| `solution` | Optional upstream reference answer or solution. Store it as text, and explain its format in the benchmark methodology. |
| `prompt_source_url` | Optional HTTPS link to the source of the task prompt. Prefer a record or file permalink. |
| `solution_source_url` | Optional HTTPS link to the source of the reference solution. |
| `environment_url` | Optional HTTPS link to readable environment setup, such as the task's official Dockerfile or setup script. Prefer a commit-pinned link. |

Omit unavailable optional fields or use `null`; do not use empty strings. The
loader supplies `benchmark_id` from the directory's metadata, so leave it out of
the JSONL records. Do not add extra fields without updating the schema and
consumers deliberately.

Some datasets split a task across several fields. Assemble all required inputs
in a documented, deterministic format while preserving their source text. For
multiple-choice tasks, retain the choice order and map the answer index to that
same order. Keep the reference answer out of the prompt. Repository tasks may
need external code and dependencies; link their setup rather than implying the
prompt alone is runnable. Image or audio inputs need explicit site support, not
just a text placeholder.

For SWE-bench Verified, `solution` is the upstream reference code patch. Its
solution source links to the original pull request's files, which may also
include tests and other changes. Its environment link points to an official
Dockerfile at a separately pinned task-repository commit. These are examples,
not assumptions to apply to other benchmarks.

## 5. Make the import reproducible

Put dataset-specific fetching and conversion in `data/<id>/import.py`. Prefer
Python's standard library where practical, following the existing importer.

- Read `benchmark.json` and honor its `dataset_revision`. Fetch that exact
  revision when supported. Otherwise verify the upstream revision before and
  after fetching, and refuse to write if it differs from the pin or changes.
- Record configuration and split choices in the importer. Paginate until the
  entire selected dataset has been fetched.
- Reject truncated or missing inputs. Require the documented reference answers
  when that dataset is expected to provide them.
- Validate the expected count and unique keys, and sort records consistently
  before writing. Repeating an import from the same revision should produce the
  same file.
- Write to a temporary file and replace `tasks.jsonl` only after validation, so
  a failed import preserves the previous snapshot.
- Verify generated source and environment links actually exist. If another
  repository supplies setup files, pin its revision separately in the importer.

Run the new importer from the repository root:

```sh
python3 data/example-benchmark/import.py
```

Inspect representative records against upstream, including long prompts,
multiline solutions, and different task formats. When refreshing an existing
benchmark, review changes to IDs, counts, and text. Updating an upstream revision
should be an intentional edit, not an automatic consequence of running a build.

## 6. Build and check

Run these commands from the repository root:

```sh
python3 scripts/build_site.py # Rebuild SQLite, validate the data, and generate dist/.
python3 scripts/check_site.py # Check generated routes, internal links, task text, solutions, and source links.
node scripts/check_ui.cjs     # Check JavaScript search, filtering, and pagination with fictional fixtures.
```

The build enforces schema constraints and the shared SQL checks: the declared
task count must match the imported count, and task keys must be unique within a
benchmark. Identical prompts are allowed because published datasets such as
MMLU contain repeated items. Investigate repeated prompts against upstream; do
not silently drop records or alter wording. Preserve distinct upstream records
under their own stable keys and document any duplicates. Read JSONL by iterating
file lines, rather than splitting text on all Unicode line separators, which
can occur inside valid task text.

`check_site.py` checks the generated site against the imported data. The UI check
tests browser logic using a fictional catalog, so adding a benchmark should not
require changing its assertions. Neither check verifies external URL availability
or replaces checking imported content against the official source. The UI check
does not check visual appearance.

## 7. Preview and review locally

If a local server is already running, rebuild and refresh it. Otherwise start one:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory dist
```

Open <http://localhost:8765> and verify:

- The benchmark appears in the index with the right name, date, and count.
- Its explanatory sections and source links are accurate.
- The task library can filter to it and search its prompts or IDs.
- Representative task pages show complete input, the correct reference solution,
  and the relevant source and environment links when available.
- Existing benchmark pages and tasks still work.

Review the diff for accidental changes to other benchmarks and generated files.
Summarize the imported scope, revision, count, checks, and any remaining gaps.
Keep development and previews local. Commit, push, or deploy only when requested.
