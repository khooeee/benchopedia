# COGS Generalization redistribution review

## Scope

Benchopedia publishes the tokenized sentences and logical forms from all
21,000 rows of the authors' `data/gen.tsv` at revision
`165a7b669eade971fa47bf568a2e51925360fed8` in the repository and on the
crawlable site. The study describes the examples as outputs of the authors'
probabilistic grammars. The scope is the corrected generalization split.
[Pinned dataset](https://github.com/najoungkim/COGS/blob/165a7b669eade971fa47bf568a2e51925360fed8/data/gen.tsv) ·
[Study, Section 3](https://aclanthology.org/2020.emnlp-main.731.pdf)

## Terms

The authors' public MIT-licensed repository identifies the files under
`data/` as the dataset used in the study. The file is downloadable without
an account or approval. The license permits copying and public redistribution
with its copyright and permission notices.
[Pinned license](https://github.com/najoungkim/COGS/blob/165a7b669eade971fa47bf568a2e51925360fed8/LICENSE) ·
[Pinned dataset documentation](https://github.com/najoungkim/COGS/blob/165a7b669eade971fa47bf568a2e51925360fed8/README.md#dataset)

## Changes

Benchopedia converts the TSV to JSONL, adds line-based task keys and source
links, and preserves the original sentence and logical-form text. The guide
uses the source's third column for case-level scores.

## Notices

COGS by Najoung Kim and Tal Linzen. The original license is included in
`LICENSE`.

```
MIT License

Copyright (c) 2020 najoungkim

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
