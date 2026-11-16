# Declined benchmark candidates

These benchmarks were considered for import and not added because the
[required redistribution review](../adding-a-benchmark.md#required-redistribution-review)
could not clear their tasks for both the public repository and the website. No
task content was copied for them. Each entry names what is unclear and what
would allow the import to resume.

## Aider Polyglot

Reviewed 2026-11-16 for all 225 exercises in
[Aider-AI/polyglot-benchmark at `7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f`](https://github.com/Aider-AI/polyglot-benchmark/tree/7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f).

The repository has no license of its own. Its README says the exercises are
copied from Exercism's C++, Go, Java, JavaScript, Python, and Rust tracks and
are copyright Exercism, whose track repositories use the MIT license. That
license can cover only text Exercism could license. The food-chain exercise,
included in the Go, Java, JavaScript, and Python sets, asks for the lyrics of
"I Know an Old Lady Who Swallowed a Fly" and reproduces the full song in its
instructions. The instructions call the song of unknown origin. Wikipedia
reports that Rose Bonne and Alan Mills copyrighted a version titled "I Know an
Old Lady" in 1952 and that Burl Ives recorded it in 1953. The exercise uses that
title and that version's lines, such as "How absurd to swallow a bird."
Neither the exercise nor the Aider README notes permission from those rights
holders. Leaving
the four exercises out would publish an incomplete set.
[README](https://github.com/Aider-AI/polyglot-benchmark/blob/7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f/README.md),
[Python food-chain instructions](https://github.com/Aider-AI/polyglot-benchmark/blob/7e0611e77b54e2dea774cdc0aa00cf9f7ed6144f/python/exercises/practice/food-chain/.docs/instructions.md),
and [Wikipedia article](https://en.wikipedia.org/w/index.php?title=There_Was_an_Old_Lady_Who_Swallowed_a_Fly&oldid=1384571605)

Resume if the lyrics' rights holders permit redistribution, the song is shown to
be in the public domain in this version, or the publishers replace the exercise
in a new release.

## DROP

Reviewed 2026-11-16 for the development set in the official
[`drop_dataset.zip`](https://ai2-public-datasets.s3.amazonaws.com/drop/drop_dataset.zip).

The passages are Wikipedia text. The paper says they were extracted from an
October 2018 Wikipedia dump and online Wikipedia, mostly NFL game summaries and
history articles. [Original paper](https://arxiv.org/abs/1903.00161)

The publishers' terms conflict. The Allen Institute's dataset page, as archived
on 2022-12-09, listed the license as
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0). That page now
redirects to an evaluation script with no license statement. The
[Hugging Face card at `95cda593fae71b60b5b19f82de3fcf3298c1239c`](https://huggingface.co/datasets/ucinlp/drop/blob/95cda593fae71b60b5b19f82de3fcf3298c1239c/README.md)
declares CC BY-SA 4.0 instead. Wikipedia text is shared under CC BY-SA, which
requires attribution to the source article and its authors. The card lists each
record's fields as a section ID, query ID, passage, question, and answers; none
names the source Wikipedia article, so Benchopedia cannot provide that
attribution.
[Archived dataset page](https://web.archive.org/web/20221209012021/https://allenai.org/data/drop)

Resume when the publisher states one set of terms for the passages and
questions, and the source Wikipedia article for each passage can be identified
for attribution.

## FOLIO

Reviewed 2026-11-16 for the validation split of FOLIO v2 in
[`yale-nlp/FOLIO` at `4c1f14bf39ca6a6de242bd8f75ef313b4b436818`](https://huggingface.co/datasets/yale-nlp/FOLIO/tree/4c1f14bf39ca6a6de242bd8f75ef313b4b436818)
and the earlier v0.0 release in
[Yale-LILY/FOLIO at `5d7bb84c7edab3fb358e057d2807f19cf5cf5e2d`](https://github.com/Yale-LILY/FOLIO/blob/5d7bb84c7edab3fb358e057d2807f19cf5cf5e2d/README.md).

The v2 dataset card declares the MIT license, but its files are gated: access
requires signing in and agreeing to share one's Hugging Face username and email
with the publishers, and anonymous requests return HTTP 401. This import does
not create that agreement on anyone's behalf, and republishing the files openly
would remove a condition the publishers chose to keep. The openly licensed v0.0
files on GitHub (CC BY-SA 4.0) are superseded; the authors' README points to v2
for "significant quality improvement and error fixing," so importing v0.0 would
publish a version with errors the authors have since fixed.

Resume if the publishers release v2 without the gate or confirm that
republishing the gated files is acceptable.

## GPQA

Reviewed 2026-11-16 for the GPQA question sets in the authors' repository at
commit `56686c06f5e19865c153de0fdb11be3890014df7` and the
[Hugging Face dataset at `83022cefff930aea54f654c0b282e74b9eeda5c6`](https://huggingface.co/datasets/Idavidrein/gpqa/tree/83022cefff930aea54f654c0b282e74b9eeda5c6).

The Hugging Face dataset is gated. Access requires agreeing "to NOT reveal
examples from this dataset in plain text or images online, to reduce the risk
of leakage into foundation model training corpora." The authors' repository
keeps the data in a password-protected `dataset.zip`, beside an MIT
license for the repository and a CC BY 4.0 declaration on the dataset
card. Publishing the questions in a public repository and on a crawlable website
would break that access condition, and the open licenses do not waive it.
[Repository README](https://github.com/idavidrein/gpqa/blob/56686c06f5e19865c153de0fdb11be3890014df7/README.md)

Resume only if the authors publish GPQA without that condition or permit
Benchopedia to publish it.

## HellaSwag

Reviewed 2026-11-16 for the validation set published in the authors' repository,
`rowanz/hellaswag`, and its
[Hugging Face copy at `218ec52e09a7e7462a5400043bb9a69a41d06b76`](https://huggingface.co/datasets/Rowan/hellaswag/tree/218ec52e09a7e7462a5400043bb9a69a41d06b76).

The paper builds many contexts by scraping how-to articles from WikiHow,
alongside ActivityNet video captions. On 2026-09-14, GitHub blocked the authors'
repository after wikiHow filed a DMCA takedown notice that lists it, asserting
copyright in wikiHow's articles. The Hugging Face copy declares no license.
Copying these contexts would publish text whose rights holder has objected to
its redistribution. [Original paper](https://arxiv.org/abs/1905.07830) and
[DMCA notice](https://github.com/github/dmca/blob/master/2026/09/2026-09-14-wikihow.md)

Resume only if wikiHow permits redistribution of the WikiHow-derived contexts,
or the dispute is resolved in a way that clears them.

## Humanity's Last Exam

Reviewed 2026-11-16 for the 2,500-question test split of
[`cais/hle` at `5a81a4c7271a2a2a312b9a690f0c2fde837e4c29`](https://huggingface.co/datasets/cais/hle/blob/5a81a4c7271a2a2a312b9a690f0c2fde837e4c29/README.md).

The dataset card declares MIT, but it also asks: "Please help us protect the
integrity of this benchmark by not publicly sharing, re-uploading, or
distributing the dataset." The data files are gated and return HTTP 401 without
an accepted access request. Republishing the questions in a public repository
and on a crawlable website would go against that request and around the gate.

The paper also reports that around 14% of questions require an image, which the
site cannot display; a text-only subset would not be the complete split.
[Paper](https://arxiv.org/abs/2501.14249)

Resume only if the publishers permit Benchopedia to publish the questions and
the site can display their images.

## MT-Bench

Reviewed 2026-11-16 for the 80 questions in
[`question.jsonl` at lm-sys/FastChat `587d5cfa1609a43d192cedb8441cac3c17db105d`](https://github.com/lm-sys/FastChat/blob/587d5cfa1609a43d192cedb8441cac3c17db105d/fastchat/llm_judge/data/mt_bench/question.jsonl)
and its GPT-4 reference answers.

The repository is offered under the
[Apache License 2.0](https://github.com/lm-sys/FastChat/blob/587d5cfa1609a43d192cedb8441cac3c17db105d/LICENSE),
but that license can cover only text its contributors could license. The second
turn of question 157 is a close paraphrase of an Analyze an Argument topic in
ETS's published GRE pool, the memo from the marketing director of Lamfonz Pet
Stores. It follows the topic sentence by sentence with the names and some words
changed, and it repeats the topic's task instruction word for word. The pool
states "Copyright © 2022 by ETS. All rights reserved." The paper says the authors
manually designed the questions, and neither it nor the MT-Bench README notes
this source or any permission from ETS. Publishing every question
would republish that adapted text, and leaving the question out would publish
an incomplete set. [GRE argument pool](https://www.ets.org/pdfs/gre/argument-pool.pdf)
and [original paper](https://arxiv.org/abs/2306.05685)

Resume if ETS permits redistribution of the adapted topic, or the publishers
replace question 157 in a new release.
