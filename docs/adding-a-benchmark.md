# Adding a benchmark

Add a benchmark by creating its metadata, tasks, and importer under `data/<id>/`.
The build discovers these directories automatically and generates the SQLite
database, benchmark page, task pages, and search index.

Use [HumanEval](../data/humaneval/) as a working example, and
[db/schema.sql](../db/schema.sql) as the authoritative field definitions. Adapt
the import to the new dataset; its identifiers, answers, and environment setup
may differ from HumanEval's.

## 1. Choose the source and scope

Start with the official dataset, project documentation, paper, and evaluation
code. Establish:

- Which variant, version, configuration, and split to include, and its task count.
- The exact upstream revision: a commit, immutable release, or file checksum.
- What input a model receives, what it must produce, and how it is evaluated.
- Whether reference solutions and task environment instructions are available.
- Whether the task data can be redistributed under its license and access terms.

### Required redistribution review

**Before downloading or importing task content, establish permission to publish
it in both the public Git repository and the crawlable website.** Review the
terms for the exact dataset revision and split, including prompts, answers,
images, code patches, and other third-party material. An evaluation harness's
license does not automatically cover its dataset or the repositories it quotes.
Public access, a citation, and Benchopedia's MIT license do not establish those
redistribution rights.

**If permission is missing, unclear, or incompatible with either form of public
redistribution, stop the import and tell the user before copying any tasks.**
Name the affected content, link the relevant terms, and explain the restriction
or uncertainty. Do not bypass access conditions, silently omit restricted items,
or treat user approval as permission from the rights holder. Resume only when
the necessary rights and obligations are documented. An original article with
upstream links may be an alternative, but an article without tasks requires an
explicit scope change and an [exclusion](#excluding-tasks). If a published
benchmark's permission turns out to be missing or unclear, exclude its tasks
the same way.

For an allowed import, record the license, immutable source links, access terms,
reviewed scope, and redistribution obligations in the benchmark's
[redistribution review](#4-write-redistribution-reviewmd), not its methodology.
Preserve required copyright notices, license texts, attribution, and any
source-availability or share-alike conditions with the imported snapshot and
published pages. Review underlying project and file licenses for code patches;
a dataset-level license label alone is insufficient. Recheck this decision when
refreshing a snapshot or changing its scope. See the
[current benchmark review](benchmark-license-review.md) for examples and open
issues. These are required manual checks; the build does not verify legal
permission.

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
    redistribution-review.md
    tasks.jsonl
    import.py
    how-to-run.md
```

`benchmark.json` contains the metadata and explanatory text.
`redistribution-review.md` records the license terms and required notices.
`tasks.jsonl` contains the imported task snapshot. `import.py` reproduces that snapshot from
the upstream source. `how-to-run.md` explains how to run and score each task. Commit these files; `build/` and `dist/` are generated and
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
  "has_solutions": true,
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

`has_solutions` must be a JSON boolean: `true` when at least one imported task
contains reference solution text, and `false` when none do. A source link or
evaluator alone does not count as a reference solution. SQLite stores this flag
as 0 or 1; the build checks it against the tasks so it stays accurate after imports.
Both `task_count` and `has_solutions` are `null` when the tasks are
[excluded](#excluding-tasks), and only then.

The overview, methodology, scoring, and limitations are sections on the benchmark
page, not separate files. Write concise explanations supported by primary sources.
Use Markdown links near factual claims and list the sources in `sources` as well.
Do not invent performance results or conclusions about saturation.

Keep license, copyright, attribution, and redistribution details out of these
sections; they belong in `redistribution-review.md`. The build fails when an
article section mentions a license or copyright.

These sections support basic Markdown: paragraphs, headings, links, and code
blocks. HTML is escaped. JSON strings represent newlines as `\n`.

## 4. Write redistribution-review.md

Record the outcome of the [redistribution review](#required-redistribution-review)
in this file. The build requires it and publishes it as the License section of
the benchmark page, so required notices appear wherever the tasks are published.
The page omits the title line and shows the `##` headings as subsections. Use the
same Markdown subset as the article sections, with absolute links, because
relative repository links do not work on the website.

```markdown
# Example Benchmark redistribution review

## Scope

What the snapshot publishes in the repository and on the website: the revision,
split, task count, and kinds of content (prompts, answers, code, images).

## Terms

The license or other grant, the rights holder, access terms, and links to the
evidence. State anything that remains unresolved.

## Changes

How Benchopedia changed the upstream material, such as added keys, assembled
prompts, or converted formats.

## Notices

Required copyright notices, license texts, attribution, and canaries,
reproduced verbatim in code blocks.
```

Keep any separate upstream license or attribution file, such as `LICENSE` or
`ATTRIBUTION.md`, beside it.

### Excluding tasks

When the tasks cannot be published, keep the benchmark's article but leave its
tasks out of both the repository and the website. Delete its `tasks.jsonl` and
`how-to-run.md`, set
`task_count` and `has_solutions` to `null`, and create
`data/<id>/exclusions.md` beside its metadata. Each affected benchmark owns its
record; there is no shared exclusion registry. The directory supplies the
benchmark ID.

```markdown
# Example Benchmark task exclusions

## Since

2026-01-01

## Reason

What is not cleared, and why.

## Restore when

The evidence or permission needed to include the tasks again.
```

The file's presence excludes the entire task snapshot. Create it only for an
excluded benchmark; a normal import does not need an empty placeholder. The
build requires nonempty `## Since`, `## Reason`, and `## Restore when` sections,
with a `YYYY-MM-DD` date under `## Since`. A malformed record fails the build
and still prevents task loading.

Explain the exclusion in the benchmark's redistribution review as well. The
build rejects a `tasks.jsonl` or `how-to-run.md` for an excluded benchmark and
requires both for every other benchmark, so tasks cannot return or disappear by
accident. Include the tasks again only after the review clears them: delete
`exclusions.md`, restore `task_count`, `has_solutions` and `how-to-run.md`, and
rerun the importer. Deleting a file
does not remove it from Git history.

## 5. Map upstream records to tasks.jsonl

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

## 6. Make the import reproducible

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

## 7. Write how-to-run.md

The benchmark page has a How to run section: steps and code that run one task
through the benchmark's own evaluation and score the result. Write it in
`data/<id>/how-to-run.md`, using `{{key}}` for the task key; the build requires
the placeholder. The page fills it in with the benchmark's first task key as an
example and tells readers to change `key` to run another task. See
[HumanEval's guide](../data/humaneval/how-to-run.md) for an example.

- Open with a short paragraph naming the official harness, scorer or metric
  definition, with a commit-pinned link. When the authors publish no scorer,
  implement the scoring rule their paper defines and say so.
- Use `###` headings for the steps: install or fetch what is needed, load this
  task, generate the model's output, and score it. Finish with a
  "Score the full benchmark" step that runs every task the official way and
  explains how per-task scores combine.
- Load the task from the upstream source and revision of the snapshot, selected
  by a `key` variable set to `"{{key}}"`. When keys differ from upstream identifiers, derive the
  identifier in code using the scheme the methodology documents. Quote `{{key}}`
  in code: keys may contain `#`, `&`, `+` and `.`.
- Represent the model as a `generate` function that raises
  `NotImplementedError` for the reader to replace. Give it the input in the
  benchmark's own prompt format, and parse its output as the official evaluation does.
- Warn when scoring executes model-generated code, and show the sandbox the
  authors recommend.

Write in the same Markdown subset as the article sections; code blocks may name
their language. Keep license and access terms in the redistribution review. Check
every command, function, file name and field against the pinned upstream source.
Where you can, run the code with the reference solution in place of the model
and confirm that it scores as correct.

## 8. Build and check

Run these commands from the repository root:

```sh
python3 scripts/build_site.py # Rebuild SQLite, validate the data, and generate dist/.
python3 scripts/check_site.py # Check generated routes, internal links, task text, solutions, and source links.
node scripts/check_ui.cjs     # Check JavaScript search, filtering, and pagination with fictional fixtures.
python3 scripts/check_exclusions.py # Check exclusion records and task-loading safeguards.
```

The build enforces schema constraints and the shared SQL checks: the declared
task count must match the imported count, task keys must be unique within a
benchmark, every benchmark needs a redistribution review, and only excluded
benchmarks may omit `tasks.jsonl` and `how-to-run.md`. Identical prompts are allowed because
published datasets such as MMLU contain repeated items. Investigate repeated prompts against upstream; do
not silently drop records or alter wording. Preserve distinct upstream records
under their own stable keys and document any duplicates. Read JSONL by iterating
file lines, rather than splitting text on all Unicode line separators, which
can occur inside valid task text.

`check_site.py` checks the generated site against the imported data. The UI check
tests browser logic using a fictional catalog, so adding a benchmark should not
require changing its assertions. Neither check verifies external URL availability
or replaces checking imported content against the official source. The UI check
does not check visual appearance.

## 9. Preview and review locally

If a local server is already running, rebuild and refresh it. Otherwise start one:

```sh
python3 -m http.server 8765 --bind 127.0.0.1 --directory dist
```

Open <http://localhost:8765> and verify:

- The benchmark appears in the index with the right name, date, and count.
- Its explanatory sections and source links are accurate, and its License section
  shows the required notices.
- Its How to run section links its example task, and its code selects that task.
- Its tasks page lists its tasks and searches their prompts or IDs.
- Representative task pages show complete input, the correct reference solution,
  and the relevant source and environment links when available.
- Existing benchmark pages and tasks still work.

Review the diff for accidental changes to other benchmarks and generated files.
Summarize the imported scope, revision, count, checks, and any remaining gaps.
Keep development and previews local. Commit, push, or deploy only when requested.
