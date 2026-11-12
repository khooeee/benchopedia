# Contributing to Benchopedia

Everything on the site is generated from plain files in `data/`. To add or fix something, edit a file and open a pull request. `npm run check` must pass.

## What counts as a benchmark

A **named, reusable way to score AI systems**: a set of tasks (fixed or versioned) plus a scoring method, published so systems can be compared. A paper is not required; a blog post or leaderboard page is enough.

Include academic datasets, private or held-out test sets, agent environments, evaluation-org evals, human-vote arenas, composite indexes, and safety or behaviour evals. Exclude standalone metrics (BLEU), evaluation harnesses (lm-eval-harness), training-only datasets and one-off case studies.

## Files

| Path | What |
|---|---|
| `data/benchmarks/<id>.md` | YAML front matter + the article |
| `data/scores/<id>.yaml` | Dated results for that benchmark |
| `data/models/<id>.yaml` | Models and systems that scores refer to |
| `data/orgs/<id>.yaml` | Benchmark publishers and model developers |
| `data/topics/<id>.md` | Topic pages; benchmarks list them in `areas` |

Ids are lowercase kebab-case and must match the file name. Use the official name with punctuation turned into hyphens (`swe-bench-verified`, `gpt-4-1`).

The schemas in `src/lib/schema/` are the source of truth. `data/benchmarks/mmlu.md`, `swe-bench-verified.md` and `honeybench.md` are worked examples.

## Benchmarks

- **summary**: one sentence, at most 240 characters, plain English.
- **publishers**: org ids, lead institution first.
- **released**: first public release (paper, post or dataset), `YYYY-MM-DD` when known.
- **measures**: `capability` (what a model can do) or `propensity` (what it tends to do).
- **format**: `dataset` (fixed questions), `agentic` (multi-step tasks with tools), `environment` (RL or robotics simulator), `arena` (human votes), `composite` (index of other benchmarks). Set `live: true` if tasks are refreshed over time.
- **metric**: the headline metric that saturation is judged on.
  - `direction`: `higher` or `lower` is better.
  - `floor`: the trivial-system score, such as random guessing (25 for four options). Omit when it is the worst end of the range.
  - `ceiling`: the best realistically achievable score. For percentages use 100 unless a source documents label errors or unsolvable items; then cite it. Omit only for open-ended metrics (Elo, time horizon, dollars), which never saturate.
- **derived_from / supersedes / related**: other benchmark ids. Store lineage only on the newer benchmark; the reverse links are computed.
- **status_override**: only for `compromised` (documented contamination or broken grading) or `saturated` when the creators themselves retire it. Always cite a source. Everything else about status is computed from scores.
- **source_keys**: names of this benchmark in imported datasets (Epoch AI, Benchmark Radar, Papers with Code), so the importer can attach scores.
- **review**: new entries are `unverified`. A person who has checked every fact against the sources sets `verified` and `verified_by`.

### Article

The body must contain these sections in order: `## What it is`, `## Example task`, `## Why it matters`, `## Caveats`, `## History`.

- Write for a smart reader who is not an ML researcher. Short paragraphs, no hype.
- **Example task**: quote a real item from the paper or dataset when possible. If you paraphrase or invent one, label it "Illustrative, in the style of …".
- **Caveats**: saturation, contamination, label errors, scaffold or prompt sensitivity, narrowness.
- **History**: dated bullets (`- **2024-06:** …`).
- Every number must come from a source you can link. Leave a field out rather than guess.

## Scores

One row per reported result. Saturation uses the latest, best rows, so dates matter.

```yaml
- model: gpt-4o-2024-05-13
  score: 33.2          # in the benchmark's metric unit (percent → 0–100)
  date: 2024-08-13     # when the result was published or measured
  reported_by: benchmark-author   # benchmark-author | model-developer | third-party
  via: epoch                      # optional: dataset the row was imported from
  source: https://openai.com/index/introducing-swe-bench-verified/
```

Optional fields: `version`, `metric` (only for non-headline metrics), `ci: [low, high]`, and `setting` (`effort`, `tools`, `scaffold`, `shots`, `note`). Reasoning effort and scaffolds go in `setting`, not in the model id.

## Models and orgs

```yaml
# data/models/gpt-4o-2024-05-13.yaml
id: gpt-4o-2024-05-13
name: GPT-4o (2024-05-13)
developer: openai
family: gpt-4o
released: 2024-05-13
open_weights: false
aliases: ["GPT-4o", "gpt-4o-2024-05-13"]
```

Use the official API id when there is one, otherwise the name from the paper. Each name or alias must belong to exactly one model.

```yaml
# data/orgs/openai.yaml
id: openai
name: OpenAI
type: lab   # academic | lab | startup | company | eval-org | nonprofit | government | community | individual
url: https://openai.com
```
