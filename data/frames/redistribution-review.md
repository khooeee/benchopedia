# FRAMES redistribution review

## Scope

The snapshot contains all 824 questions in test.tsv at revision `58d9fb6330f3ab1316d1eca12e5e8ef23dcc22ef` of the google/frames-benchmark dataset, its only data file. For each question it includes the question, the gold answer, and the Wikipedia links listed for it, all English text. The reasoning-type labels are not included, and no Wikipedia article text is copied beyond what the questions, answers, and links themselves contain. Both the public repository and the website publish this content. No code or images are copied. [Dataset files](https://huggingface.co/datasets/google/frames-benchmark/tree/58d9fb6330f3ab1316d1eca12e5e8ef23dcc22ef)

## Terms

The dataset card at the pinned revision declares the Apache License 2.0 for the dataset, which Google publishes under its own Hugging Face organization. The repository has no separate LICENSE or NOTICE file. Apache 2.0 permits copying, redistribution, and modified versions when a copy of the license is included, modified files carry notices that they were changed, and any NOTICE file is kept. The license text is kept beside this review as LICENSE. The dataset has no access gate. [Dataset card](https://huggingface.co/datasets/google/frames-benchmark/blob/58d9fb6330f3ab1316d1eca12e5e8ef23dcc22ef/README.md)

The paper says human annotators wrote the questions and answers and recorded the Wikipedia articles they used. The questions and answers state facts from those articles in the annotators' own words, though some longer answers closely paraphrase article sentences. Fifteen links end in a #:~:text= fragment that repeats a few words from the start and end of a Wikipedia passage. Wikipedia text is available under the Creative Commons Attribution-ShareAlike 4.0 license, which permits redistribution when the article is credited, for example by a link, and requires adaptations to stay under the same terms. Each task keeps the links to the articles its question draws on. No other third-party content was found. [Paper](https://arxiv.org/abs/2409.12941) and [Wikipedia's reuse terms](https://en.wikipedia.org/wiki/Wikipedia:Reusing_Wikipedia_content)

## Changes

Benchopedia stores each question as the task prompt. It builds each reference answer from the gold answer, a label, and the question's link cells, one per line, and builds IDs from the upstream row index. It also adds source links. Question, answer, and link text is unchanged.

## Notices

FRAMES is from "Fact, Fetch, and Reason: A Unified Evaluation of Retrieval-Augmented Generation" by Satyapriya Krishna, Kalpesh Krishna, Anhad Mohananey, Steven Schwarcz, Adam Stambler, Shyam Upadhyay, and Manaal Faruqui. It is used under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0), kept in full beside this review as LICENSE.

The questions and answers draw on Wikipedia articles by Wikipedia contributors. Any Wikipedia text they contain remains available under the [Creative Commons Attribution-ShareAlike 4.0 International license](https://creativecommons.org/licenses/by-sa/4.0/legalcode). Benchopedia's MIT license does not replace those terms.
