# Benchopedia

The encyclopedia of AI benchmarks: one readable page per benchmark, with an at-a-glance view of which benchmarks are saturated and which still have headroom.

## How it works

For the full import and verification process, see [Adding a benchmark](docs/adding-a-benchmark.md).

`data/` is the source of truth: one directory per benchmark, holding `benchmark.json` and `tasks.jsonl`.

```sh
python3 scripts/helpers/build_sqlite.py
```

loads everything into `build/benchopedia.db` (SQLite) and fails if any constraint in `db/schema.sql` or any check query is violated. A check is a `SELECT` that returns the rows breaking a rule; shared checks live in `checks/`.

`scripts/build_site.py` calls this helper automatically before generating the website.

`data/<benchmark>/import.py` re-snapshots a benchmark's tasks from its upstream dataset.

## Schema

`db/schema.sql` is authoritative, including the `CHECK` constraints not shown here.

```mermaid
erDiagram
    benchmark ||--o{ task : contains

    benchmark {
        TEXT id PK "its directory name under data/"
        TEXT name UK
        TEXT summary
        TEXT homepage_url
        TEXT dataset_url
        TEXT dataset_revision "upstream revision imported"
        TEXT released_on "YYYY-MM-DD"
        INTEGER task_count "declared size, null if excluded"
        INTEGER has_solutions "boolean, null if excluded"
        TEXT overview "article section"
        TEXT methodology "article section"
        TEXT scoring "article section"
        TEXT limitations "article section"
        TEXT redistribution_review "License section"
        TEXT sources "JSON array"
    }
    task {
        TEXT benchmark_id PK, FK
        TEXT key PK "the benchmark's own identifier"
        TEXT prompt "what the model is given"
        TEXT solution "reference solution, nullable"
        TEXT environment_url "nullable"
        TEXT solution_source_url "nullable"
        TEXT prompt_source_url "nullable"
    }
```

## Build the website

```sh
python3 scripts/build_site.py # Rebuild and validate SQLite, then generate the website in dist/.
python3 scripts/check_site.py # Check generated pages, links, prompts and solutions.
node scripts/check_ui.cjs     # Test search, filters, and pagination without a browser.
python3 scripts/check_exclusions.py # Check exclusion records and task-loading safeguards.
python3 -m http.server 8765 --directory dist
```

Open http://localhost:8765. Python 3.9+ with SQLite 3.37+ is required; there are no
third-party build dependencies. JavaScript adds search, filters and
pagination. Articles and every task also have their own static HTML pages.
The optional UI checks use Node.js and exercise the browser logic with fictional
fixtures, without external test packages or a generated site. They do not depend
on which benchmarks have been imported.

The website build first rebuilds and validates SQLite, then reads it to generate
`dist/`. It includes the benchmark index, article pages, a searchable task list
for each benchmark, individual task pages, and reference solutions when available. Generated files and the
database are ignored by Git.

The interface is a compact archive: benchmarks listed by release year, numbered
task lists, and single-column reference pages. All fonts and assets are local.

`assets/` holds the stylesheet and browser code. `scripts/build_site.py`
holds the page templates. `benchmark.json` also holds the benchmark's article:
its overview, methodology, scoring and limitations sections and its primary
sources. `redistribution-review.md` holds its license terms and required
notices, published as the page's License section. Article text supports
paragraphs, headings, code blocks, inline code and HTTP(S) links. Source HTML
is escaped.

To add a benchmark, add its metadata, article, redistribution review and tasks
under `data/<id>/`,
then rebuild. Counts, navigation
and search indexes are generated from the database. Each task stores its
benchmark link, key, prompt, optional reference solution, and optional URLs for
the prompt source, task environment and solution source.

Model results and saturation indicators await sourced score data.

## Licensing

Benchopedia's original code and documentation are available under the
[MIT license](LICENSE). Imported benchmark content retains its upstream
copyrights and license or access terms; the root license does not replace them.
See each benchmark's `redistribution-review.md` and the
[benchmark license review](docs/benchmark-license-review.md) for the reviewed
terms and unresolved issues. A benchmark’s optional `data/<id>/exclusions.md`
records why its tasks are left out and what is required to restore them.

## Deployment

GitHub Pages serves the generated `dist/` directory at
https://khooeee.github.io/benchopedia/.
The GitHub Actions workflow builds the website and runs both checks on pull
requests. It publishes only from `main`, after all checks pass; pull requests
never publish a preview. Development and previews stay local.

See [Deployment setup](docs/deployment.md) for the GitHub Pages and Cloudflare
settings, optional custom domains, and manual redeployment.
