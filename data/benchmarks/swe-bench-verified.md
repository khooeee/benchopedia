---
id: swe-bench-verified
name: SWE-bench Verified
aliases: ["SWE-Bench Verified", "SWE-bench_Verified"]
summary: 500 real GitHub issues from SWE-bench, screened by engineers, where the model must write a patch that passes hidden tests.
publishers: [openai, princeton]
released: 2024-08-13
areas: [coding, agents]
tags: [software-engineering, repository-level, python]
measures: capability
format: agentic
modality: [text]
openness: public
size: { items: 500, unit: issues, note: "human-validated subset of the 2,294-issue SWE-bench test set" }
metric:
  name: resolved
  unit: percent
  direction: higher
  ceiling:
    value: 100
    note: "OpenAI's 2026 audit found many unsolved problems had flawed tests, so the practical ceiling is below 100%"
    source: https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/
derived_from: [swe-bench]
related: [swe-bench-pro, terminal-bench]
links:
  website: https://www.swebench.com
  blog: https://openai.com/index/introducing-swe-bench-verified/
  dataset: https://huggingface.co/datasets/SWE-bench/SWE-bench_Verified
  code: https://github.com/SWE-bench/SWE-bench
status_override:
  status: compromised
  reason: "OpenAI stopped reporting it in February 2026, citing contamination (models reproduced original fixes from memory) and flawed tests that reject correct solutions."
  source: https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/
source_keys:
  radar: ["llm-stats:swe-bench-verified"]
review: { state: unverified, drafted_by: llm }
---

## What it is

SWE-bench Verified is a 500-problem subset of SWE-bench. Each problem is a real GitHub issue from a popular Python repository such as Django or scikit-learn. The model gets the repository at the commit before the fix and must produce a patch; it counts as resolved if the project's hidden tests for that issue pass and no existing tests break.

OpenAI's Preparedness team built it with the SWE-bench authors by having professional developers screen SWE-bench problems and remove those with underspecified issues or unfair tests.

## Example task

The model receives an issue such as "`separability_matrix` does not compute separability correctly for nested CompoundModels" from the `astropy` repository, plus the full codebase. It must locate the bug, edit the source and return a diff. Hidden tests written by the original maintainers decide whether the fix is correct.

## Why it matters

From 2024 to early 2026 it was the standard measure of agentic coding ability and appeared in nearly every frontier model announcement. Scores rose from about 33% (GPT-4o at launch) to the high 70s and beyond, tracking the rise of coding agents.

## Caveats

- **Compromised.** In February 2026 OpenAI stopped reporting it and recommended others do the same. Its audit found that frontier models could reproduce some original fixes from memory, and that many unsolved problems had tests that reject correct solutions.
- **Scaffold-dependent.** Results depend heavily on the agent harness, number of attempts and tool access, so scores from different sources are not directly comparable.
- **Narrow.** Only Python, only 12 repositories, and mostly small bug fixes.

## History

- **2023-10:** SWE-bench (2,294 issues) released by Princeton researchers.
- **2024-08:** SWE-bench Verified released by OpenAI and the SWE-bench authors.
- **2025:** Becomes the headline coding number for frontier releases.
- **2026-02:** OpenAI publishes "Why we no longer evaluate SWE-bench Verified" and recommends SWE-bench Pro instead.
