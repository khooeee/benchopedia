---
id: mmlu
name: MMLU
aliases: ["Massive Multitask Language Understanding", "Measuring Massive Multitask Language Understanding"]
summary: Four-option multiple-choice exam across 57 subjects, from elementary maths to law and medicine.
publishers: [uc-berkeley, columbia, uchicago, uiuc]
released: 2020-09-07
areas: [knowledge]
tags: [multiple-choice, exams, general-knowledge]
measures: capability
format: dataset
modality: [text]
openness: public
size: { items: 15908, unit: questions, note: "57 subjects; 14,042 in the test split" }
metric:
  name: accuracy
  unit: percent
  direction: higher
  floor: { value: 25, note: "random guessing among four options" }
  ceiling:
    value: 93.5
    note: "MMLU-Redux re-annotation estimated about 6.5% of questions contain errors"
    source: https://arxiv.org/abs/2406.04127
human_baseline: { value: 89.8, note: "estimated expert-level accuracy from the paper; non-expert crowdworkers scored 34.5%", source: https://arxiv.org/abs/2009.03300 }
related: [mmlu-pro, mmlu-redux]
links:
  paper: https://arxiv.org/abs/2009.03300
  code: https://github.com/hendrycks/test
  dataset: https://huggingface.co/datasets/cais/mmlu
source_keys:
  epoch: ["MMLU"]
  radar: ["llm-stats:mmlu"]
review: { state: unverified, drafted_by: llm }
---

## What it is

MMLU is a multiple-choice exam with 15,908 questions covering 57 subjects, including elementary mathematics, US history, computer science, law, medicine and ethics. Each question has four options, and a model is scored by how many it answers correctly, usually with five worked examples in the prompt.

## Example task

Illustrative, in the style of the high-school biology subset:

> Which organelle is the main site of ATP production in eukaryotic cells?
> (A) Ribosome (B) Mitochondrion (C) Golgi apparatus (D) Lysosome

The model must output the letter of the correct option (B).

## Why it matters

For several years MMLU was the headline number in almost every language-model release, because it was broad, cheap to run and hard for early models. GPT-3 scored about 44% when the benchmark was released, against 25% for random guessing. It became the reference point for "general knowledge" and spawned many successors and translations.

## Caveats

- **Saturated.** Frontier models score around 90%, close to the ceiling set by label errors, so differences between them are mostly noise.
- **Label errors.** The MMLU-Redux re-annotation found that roughly 6.5% of questions have wrong answers, unclear wording or multiple correct options. Some subjects, such as virology, are far worse.
- **Contamination.** The questions have been public since 2020 and appear widely on the web, so they are very likely in training data.
- **Prompt sensitivity.** Scores move by several points depending on prompt format, number of examples and answer extraction, which makes cross-lab comparisons unreliable.

## History

- **2020-09:** Released by Dan Hendrycks and collaborators; published at ICLR 2021.
- **2023–2024:** Becomes the default headline benchmark; top scores pass 85%.
- **2024-06:** MMLU-Pro (harder, ten options) and MMLU-Redux (corrected subset) are released in response to saturation and label errors.
- **2025 onward:** Most frontier labs stop reporting MMLU in favour of MMLU-Pro, GPQA and Humanity's Last Exam.
