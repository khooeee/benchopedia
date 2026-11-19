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

## BIG-Bench Hard

Reviewed 2026-11-19 for all 6,511 examples in the 27 files of `bbh/` in
[suzgunmirac/BIG-Bench-Hard at `9ee07bd481feebf959a6b59d61ea57bdcf30964d`](https://github.com/suzgunmirac/BIG-Bench-Hard/tree/9ee07bd481feebf959a6b59d61ea57bdcf30964d/bbh).
The 23 tasks are taken from
[google/BIG-bench, read at `092b196c1f8f14a54bbc62f24759d43bde46dd3b`](https://github.com/google/BIG-bench/tree/092b196c1f8f14a54bbc62f24759d43bde46dd3b/bigbench/benchmark_tasks),
whose task descriptions record where each task's material came from.

The BBH repository carries the MIT license, with the notice "Copyright (c) 2022
suzgunmirac", and BIG-bench carries the Apache 2.0 license. Either can cover
only material its contributors could license. Four of the tasks are built from
material by others, and neither repository records permission for it:

- `movie_recommendation` (250 examples) is derived from the MovieLens ratings
  dataset. MovieLens may be used "for any research purposes" on conditions that
  include: "The user may redistribute the data set, including transformations,
  so long as it is distributed under these same license conditions" and "The
  user may not use this information for any commercial or revenue-bearing
  purposes without first obtaining permission". Publishing the questions would
  carry a research-only, non-commercial condition that neither the repository
  nor the website carries.
- `causal_judgement` (187 examples) consists of stories its authors
  "collected ... from 30 papers published in the span of 1989 to 2021", in
  psychology and philosophy journals and books from publishers including the
  American Psychological Association, Elsevier, Springer, and Wiley. Each
  BIG-bench record names its paper and experiment, such as Experiment 1,
  Vignette 3 of Icard, Kominsky, and Knobe's 2017 paper "Normality and actual
  causal strength", and some note a "Small modification".
- `snarks` (178 examples) starts from Reddit comments: "we scrape sentences
  from publicly available Reddit data, flagging comments with the “/s” token
  (indicating sarcasm) as candidates for inclusion", which are then paired with
  minimally edited versions.
- `ruin_names` (250 examples) was "curated from tweets associated with the
  hashtags #RuinAFilmTitle and #RuinABandName".

A fifth task, `salient_translation_error_detection`, translates German
Wikipedia sentences drawn from the WIT dataset, which its description says is
available under CC BY-SA 3.0. That condition could be met by sharing those
examples under the same license, but BBH distributes them under MIT without it.

Together the four tasks hold 865 of the 6,511 examples. Leaving them out would
publish a reduced set in place of the full benchmark.
[BBH license](https://github.com/suzgunmirac/BIG-Bench-Hard/blob/9ee07bd481feebf959a6b59d61ea57bdcf30964d/LICENSE),
[movie_recommendation](https://github.com/google/BIG-bench/blob/092b196c1f8f14a54bbc62f24759d43bde46dd3b/bigbench/benchmark_tasks/movie_recommendation/README.md),
[MovieLens usage license](https://files.grouplens.org/datasets/movielens/ml-latest-small-README.html),
[causal_judgment](https://github.com/google/BIG-bench/blob/092b196c1f8f14a54bbc62f24759d43bde46dd3b/bigbench/benchmark_tasks/causal_judgment/README.md),
[snarks](https://github.com/google/BIG-bench/blob/092b196c1f8f14a54bbc62f24759d43bde46dd3b/bigbench/benchmark_tasks/snarks/README.md),
[ruin_names](https://github.com/google/BIG-bench/blob/092b196c1f8f14a54bbc62f24759d43bde46dd3b/bigbench/benchmark_tasks/ruin_names/README.md),
and [salient_translation_error_detection](https://github.com/google/BIG-bench/blob/092b196c1f8f14a54bbc62f24759d43bde46dd3b/bigbench/benchmark_tasks/salient_translation_error_detection/README.md)

Resume if GroupLens permits publishing the movie questions without the
research-only condition, the rights holders of the papers, comments, and tweets
behind the other three tasks are shown to permit redistribution, or a new BBH
release replaces those tasks.

## CodeContests

Reviewed 2026-11-17 for the 165-problem test split of
[google-deepmind/code_contests at `fa7a4f8139aab08362503f3344778eb86901709a`](https://github.com/google-deepmind/code_contests/tree/fa7a4f8139aab08362503f3344778eb86901709a).

Every problem in that split comes from Codeforces. Each record carries a
`source` field whose values are the enum in `contest_problem.proto`, where
`CODEFORCES = 2`, and all 165 test rows hold that value, read row by row from
the Hugging Face mirror at revision `802411c3010cb00d1b05bad57ca77365a3c699d6`;
the problems are named for their Codeforces contest and index, beginning
`1575_A. Another Sorting Problem`. There is no part of the split that avoids the
question below.
[Problem definition](https://github.com/google-deepmind/code_contests/blob/fa7a4f8139aab08362503f3344778eb86901709a/contest_problem.proto)
and [mirror at that revision](https://huggingface.co/datasets/deepmind/code_contests/tree/802411c3010cb00d1b05bad57ca77365a3c699d6)

The publisher declares terms and then withdraws them for exactly this material.
The README licenses the code under Apache 2.0 and says "All non-code materials
provided are made available under the terms of the CC BY 4.0 license". It then
records that "Codeforces materials are sourced from http://codeforces.com" and
closes: "Use of the third-party software, libraries code or data may be governed
by separate terms and conditions or license provisions. Your use of the
third-party software, libraries or code may be subject to any such terms. We
make no representations here with respect to rights or abilities to use any such
materials." The problem statements are that third-party data, so the declaration
is not a statement that DeepMind could license them.
[README at the pinned commit](https://github.com/google-deepmind/code_contests/blob/fa7a4f8139aab08362503f3344778eb86901709a/README.md#license)

Codeforces itself grants no public right to republish. Its current Terms and
Conditions, a binding agreement with CODEFORCES GLOBAL - FZCO, say "You are
expressly and emphatically restricted from all of the following: selling,
sublicensing and/or otherwise commercializing any Website material", and the
only content license they describe runs from a user to Codeforces, not from
Codeforces to the public. Benchopedia's repository is under the MIT license,
which would purport to sublicense the statements to anyone who clones it.
[Terms and Conditions](https://codeforces.com/terms), as
[archived on 2026-11-04](https://web.archive.org/web/20261104183935/https://codeforces.com/terms)

The one permission Codeforces has published is old and written against this use.
A 2010 blog post by MikeMirzayanov sets out a "Codeforces materials usage
license (v. 0.1)" whose first paragraph reads: "You may publish the texts of
Codeforces problems in any open sources, but you must preserve a direct link to
the site http://codeforces.ru (http://codeforces.com for English statements) and
indicate Codeforces as the problem source. These data should be located in the
close proximity to the statement, be easily noticeable and readable. It is
forbidden to publish Codeforces problems in open sources supporting automatic
testing (such as online judges or similar resources)." The second paragraph adds
"You must not use tests and other materials of the problems (generators,
checkers, validators) to publish tasks in open sources supporting automatic
testing (such as online judges or similar resources) even provided the original
problem conditions has been changed", and the third requires that "The secondary
(subsequent) distribution of the tasks should contain this license and comply
fully with the license's rules". A
benchmark catalog publishes these problems so that programs can be tested
against them automatically, and the tests are what makes the dataset scorable,
so both restrictions bear on the import; the share-alike-style third paragraph
also cannot be reconciled with the repository's MIT grant. The post calls the
text version 0.1 and says "we will perhaps change a lot in it", a comment asking
whether it is still current drew no reply, and the terms page above is the site's
present statement.
[Problems' Materials Publishing](https://codeforces.com/blog/entry/967), as
[archived on 2025-12-19](https://web.archive.org/web/20251219042748/https://codeforces.com/blog/entry/967)

Two practical obstacles were noted and are not the reason for the decline: the
published files are Riegeli protobuf records that the repository reads with
bazel, and the Hugging Face mirror ships Parquet, so an importer would need a
reader beyond Python's standard library.

Resume if Codeforces states, in its terms or in a grant it confirms is current,
that problem statements and tests may be republished by others, including from a
repository under a permissive license; or if the publishers release a split whose
problems come only from sources that grant that.

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

## HarmBench

Reviewed 2026-11-17 for the 320 text behaviors in
[`data/behavior_datasets/harmbench_behaviors_text_test.csv` at centerforaisafety/HarmBench `8e1604d1171fe8a48d8febecd22f600e462bdcdd`](https://github.com/centerforaisafety/HarmBench/blob/8e1604d1171fe8a48d8febecd22f600e462bdcdd/data/behavior_datasets/harmbench_behaviors_text_test.csv).

The repository is offered under the
[MIT license](https://github.com/centerforaisafety/HarmBench/blob/8e1604d1171fe8a48d8febecd22f600e462bdcdd/LICENSE),
but that license can cover only text its contributors could license. Of the
320 behaviors, 81 are contextual: each pairs a request with a context string,
and those 81 strings hold about 110,000 characters of material the authors did
not write. Eleven behaviors describe their context as a section or paragraphs
of a named Wikipedia article, so that text is shared under CC BY-SA and
requires attribution to the article and its authors. Others present excerpts
the behavior attributes to published research papers, and others present
third-party program source code. The file's columns are the behavior, its
categories, tags, context string, and ID; none records where a context string
came from or under what terms, so Benchopedia cannot supply the attribution
CC BY-SA requires or establish permission for the rest. This is the same gap
that stopped the DROP import. Publishing every behavior would republish that
material, and leaving the 81 contextual behaviors out would publish an
incomplete split. [Original paper](https://arxiv.org/abs/2402.04249)

The 80 copyright behaviors do not raise this problem: they name a book or song
and ask a model to reproduce it, and the repository ships hashes of the
original works for its classifier rather than their text.

A second reason stands on its own. The paper says the contextual behaviors are
included to be "differentially harmful", meaning the request cannot be carried
out with a search engine, and reports a 0% searchability rate for them against
50% and 55% for two earlier behavior datasets. Their context strings
accordingly supply specific operational detail, and several target named
individuals. Benchopedia publishes every imported prompt in a public
repository and on a crawlable website, which is not an appropriate venue for
that material even where the terms allow it. A red-teaming set of this kind
needs the controlled distribution its publishers use, not a catalog page.

Resume only if the publishers record a redistributable source and terms for
each context string, and a way to publish the behaviors that does not put the
contextual material on a crawlable page.

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

## QASPER

Reviewed 2026-11-17 for the test split in the publishers'
[`qasper-test-and-evaluator-v0.3.tgz`](https://qasper-dataset.s3.us-west-2.amazonaws.com/qasper-test-and-evaluator-v0.3.tgz),
SHA-256 `72a52a41193e2838b8074f80ac074b94f956b84886c36a61c58a7df4171bdd72`. Its
`qasper-test-v0.3.json` holds 1,451 questions about 416 research papers, and
with them the papers themselves: 20,221 paragraphs, about 9.9 million
characters of text. The questions are only answerable from those papers, so an
import has to publish them.

The dataset card declares
[CC BY 4.0](https://huggingface.co/datasets/allenai/qasper/blob/fdc9d8214fbab5dd782958601db4d678e6934a54/README.md),
and the Allen Institute's dataset page now redirects to that card. That
declaration can cover only text the publishers could license. The paper says
the full text comes from S2ORC and that the authors "have restricted ourselves
to arXiv papers released under a CC-BY-* license, as identified via Unpaywall".
Unpaywall reports the license of a paper's open-access published version, which
for these computational linguistics papers is usually the ACL Anthology copy,
while the text in this file was parsed from each paper's arXiv LaTeX source.
Those two versions are not the same document and need not carry the same terms.
[Original paper](https://arxiv.org/abs/2105.03011)

The arXiv versions are mostly not openly licensed. For a random 60 of the 416
test papers, the license arXiv records for the version it distributes was 54
times the arXiv perpetual non-exclusive license, 4 times CC BY 4.0, once
CC BY-SA 4.0, and once CC BY-NC-SA 4.0. The non-exclusive license is the
submission default and reads in full: "I grant arXiv.org a perpetual,
non-exclusive license to distribute this article." It grants that license to
arXiv and conveys no redistribution right to anyone else, so for roughly nine
in ten of these papers nothing in the chain permits Benchopedia to publish the
text. The CC BY-NC-SA paper, arXiv 1912.10162, adds a non-commercial condition
that neither the repository nor the website carries. S2ORC, the corpus the text
was taken from, was released under a non-commercial license when QASPER was
built and now asks users to "double-check whether their intended usage of S2ORC
and its underlying contents is permissible".
[arXiv license](https://arxiv.org/licenses/nonexclusive-distrib/1.0/),
[arXiv metadata interface](https://export.arxiv.org/oai2?verb=GetRecord&identifier=oai:arXiv.org:1911.10742&metadataPrefix=arXiv),
and [S2ORC README](https://github.com/allenai/s2orc/blob/master/README.md#license)

Publishing the split would republish 416 papers whose own terms mostly do not
allow it. Keeping only the papers that clear would publish a fraction of the
split, and keeping the questions without the papers would publish tasks whose
input is missing. The split's own README also asks readers to "make sure you
access the test file only to evaluate your finalized model", which a catalog
page does not do.

Resume if the publishers record a redistributable license for each paper and
those licenses permit publishing the papers' text in a public repository and on
a crawlable website, or if they release a version drawn only from papers whose
arXiv licenses allow it.

## QuALITY

Reviewed 2026-11-17 for the development split, the evaluation split whose
answers are released, in
[`QuALITY.v1.0.1.dev` at nyu-mll/quality `f84977c40dbfef70c9cab48037b7becfc8e45f73`](https://github.com/nyu-mll/quality/blob/f84977c40dbfef70c9cab48037b7becfc8e45f73/data/v1.0.1/QuALITY.v1.0.1.dev).
It holds 2,086 multiple-choice questions written by readers of 115 articles
averaging about 5,000 tokens, and the articles themselves, which the questions
cannot be answered without.

The leaderboard page the repository publishes says "QuALITY is distributed under
a CC BY 4.0 License", and the paper says the authors used "only sources that are
licensed under CC-BY (or more permissive licenses)". The records themselves
contradict that for one of their sources. Each record names the article's
license: 86 of the 115 development articles are Project Gutenberg texts in the
United States public domain, 10 are published under CC BY 4.0 by The Long+Short,
MIT Press, and Freesouls, and 19 are Slate magazine articles from 1996 to 2000
whose license field is the end-user agreement of the Open American National
Corpus. 351 of the 2,086 questions are about those 19 articles.
[Leaderboard page](https://github.com/nyu-mll/quality/blob/f84977c40dbfef70c9cab48037b7becfc8e45f73/docs/index.html)
and [original paper](https://arxiv.org/abs/2112.08608)

That agreement is not CC BY or more permissive. It records that "the copyright
to each segment comprising the O-ANC Texts is held by its author(s) or
designee(s)", grants the end user a "non-exclusive, non-transferable" license,
and allows redistribution of excerpted or reformatted text only as a
"transparent modification" on conditions including that "the text of this
Agreement must be displayed in human-readable form", that the modification be
labelled with who made it and when, and that "the location of the original
unmodified document must be identified". QuALITY shortened its articles to
6,000 words, and the url field, which records where every other article came
from, is empty for all 38 Slate question sets, so that last condition cannot be
met from the data. The agreement also forbids distributing substantively
modified versions without the copyright holders' written permission and asks
licensees to delete the material when a project becomes inactive, which is not
how a permanent public catalog works. Publishing these articles under CC BY 4.0
would relicense Slate's journalism on terms the corpus cannot grant, and
leaving the 19 articles out would publish an incomplete split.
[OANC license](https://www.anc.org/OANC/license.txt)

The Gutenberg and CC BY articles raise no such problem, and the questions and
options are the authors' own work under their CC BY 4.0 declaration.

Resume if the publishers replace the Slate articles with text they can license
under CC BY, or if Slate or the corpus consortium permits publishing those
articles in a public repository and on a crawlable website.

## WebArena

Reviewed 2026-11-16 for all 812 tasks in
[`config_files/test.raw.json` at web-arena-x/webarena `dce04686a56253aefba7b18a4fa0937cf1dc987b`](https://github.com/web-arena-x/webarena/blob/dce04686a56253aefba7b18a4fa0937cf1dc987b/config_files/test.raw.json).

The repository is offered under the
[Apache License 2.0](https://github.com/web-arena-x/webarena/blob/dce04686a56253aefba7b18a4fa0937cf1dc987b/LICENSE),
but that license can cover only text its contributors could license. The paper
says the shopping site's roughly 90,000 products, including their reviews, were
imported from real online stores, such as the Amazon product data in the
WebShop data dump. Tasks 163, 165, and 167 ask for the main criticisms of a
product, and each reference answer quotes six sentences from that product's
customer reviews word for word. The reviewers or Amazon hold the rights in that
text. Neither the paper nor the WebArena README notes permission to
redistribute it. Publishing every task would republish the review excerpts, and
leaving the three tasks out would publish an incomplete set.
[Original paper](https://arxiv.org/abs/2307.13854) and
[README](https://github.com/web-arena-x/webarena/blob/dce04686a56253aefba7b18a4fa0937cf1dc987b/README.md)

Resume if the publishers replace those reference answers with text they can
license, or the review text is shown to be cleared for redistribution.
