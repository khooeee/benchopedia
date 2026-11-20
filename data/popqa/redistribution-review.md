# PopQA redistribution review

## Scope

The snapshot contains all of PopQA: the 14,267 questions in `data/popQA.tsv`
at commit `8172ab04794a1651488207c230286b0b3786d736` of
AlexTMallen/adaptive-retrieval. For each question it includes the question
text and its list of accepted answers. The file's other columns, including the
subject and object, their Wikidata links, and the popularity counts, are not
copied, nor are the repository's code, figures, and notebook. Both the public
repository and the website publish this content. It is text only, with no code
or images.
[Data file at the pinned commit](https://github.com/AlexTMallen/adaptive-retrieval/blob/8172ab04794a1651488207c230286b0b3786d736/data/popQA.tsv)

## Terms

The repository's `LICENSE` at the pinned commit is the MIT License, with the
notice "Copyright (c) 2023 Alex Mallen", and GitHub identifies the
repository's license as MIT. The file was added on 2023-01-21. The data file
was added in the repository's first commit on 2022-12-20 and has not changed
since. The license permits anyone to use, copy, modify, publish, and
distribute the repository's files, provided the copyright notice and
permission notice are included with all copies or substantial portions. It
adds no non-commercial, share-alike, or research-only condition. The file is
downloaded directly from GitHub with no form, account, or click-through terms.
[License at the pinned commit](https://github.com/AlexTMallen/adaptive-retrieval/blob/8172ab04794a1651488207c230286b0b3786d736/LICENSE)
and [history of the data file](https://github.com/AlexTMallen/adaptive-retrieval/commits/8172ab04794a1651488207c230286b0b3786d736/data/popQA.tsv)

The license covers the dataset. In the ACL 2023 paper's checklist, asked
whether they discussed the license or terms for use and distribution of their
artifacts, the authors answer: "The license is in our GitHub repository". On
2025-07-02 the first author added a Creative Commons Attribution 4.0 license
file to the repository and deleted it a minute later with the message
"LICENSE already exists", which is the pinned commit; the MIT `LICENSE`
remains the repository's only license. The README states no other terms and
asks users to cite the paper, which is credited below. The authors'
Hugging Face copy, `akariasai/PopQA`, declares no license and is not gated.
[Paper](https://aclanthology.org/2023.acl-long.546/),
[the pinned commit](https://github.com/AlexTMallen/adaptive-retrieval/commit/8172ab04794a1651488207c230286b0b3786d736),
[README](https://github.com/AlexTMallen/adaptive-retrieval/blob/8172ab04794a1651488207c230286b0b3786d736/README.md),
and [Hugging Face copy](https://huggingface.co/datasets/akariasai/PopQA)

The questions are generated from the authors' own templates, one per
relationship type, filled with the names of Wikidata entities. The answers are
the labels and aliases of Wikidata entities. The paper's checklist says the
dataset contains only data from Wikidata, and Wikidata makes its structured
data available under Creative Commons CC0, which places no conditions on
reuse.
[Wikidata licensing](https://www.wikidata.org/wiki/Wikidata:Licensing)

Many questions name real people, mostly public figures such as authors,
directors, politicians, and athletes, and ask facts Wikidata records about
them, including occupation, birthplace, religion, and parents. These are the
public facts published in Wikidata. A scan of the imported text found no
contact details or web addresses.

## Changes

Each task prompt is the question exactly as published. The reference solution
is the question's `possible_answers` list, one answer per line in the
published order, with an alias that repeats within a list kept once. Keys are
the file's `id` values, and source links point at the data file at the pinned
commit.

The grader in `eval.py` reproduces the correctness test of the repository's
`run_model.py`, under the same license.

## Notices

PopQA is from "When Not to Trust Language Models: Investigating Effectiveness
of Parametric and Non-Parametric Memories" by Alex Mallen, Akari Asai, Victor
Zhong, Rajarshi Das, Daniel Khashabi, and Hannaneh Hajishirzi, Proceedings of
the 61st Annual Meeting of the Association for Computational Linguistics
(Volume 1: Long Papers), pages 9802–9822, 2023, published in the
AlexTMallen/adaptive-retrieval repository. Its license, which accompanies this
snapshot as `LICENSE`:

```
MIT License

Copyright (c) 2023 Alex Mallen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

PopQA carries no canary string.
