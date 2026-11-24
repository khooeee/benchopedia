# WinoBias redistribution review

## Scope

Benchopedia publishes the numbered tokens and reference clusters from all four WinoBias CoNLL test files, with 396 documents in each file. The repository and website use the same 1,584 documents. The archive also contains development data, resources for debiasing, and tools for use with separately obtained OntoNotes material. Those resources are outside this snapshot. [Pinned test files](https://github.com/uclanlp/corefBias/tree/0bce984dd081bbc10b0622f326727a024c607895/WinoBias/wino/data/conll_format)

## Terms

The UCLA NLP authors identify the data directory as the WinoBias corpus they generated. Their project publishes it under the MIT license, which permits copying, modification, and public redistribution with the copyright and permission notices retained. The four reviewed files are publicly accessible without authentication, agreements, or access gates. [Authors’ dataset README](https://github.com/uclanlp/corefBias/blob/0bce984dd081bbc10b0622f326727a024c607895/WinoBias/wino/readme.md) [Pinned MIT license](https://github.com/uclanlp/corefBias/blob/0bce984dd081bbc10b0622f326727a024c607895/LICENSE)

The local setup downloads the separate CoNLL v8.01 scorer and its dependencies directly from their pinned source with checksum verification. Benchopedia publishes its own Python adapter. The scorer’s repository and bundled Perl modules retain their original terms at the download source. [Scorer repository license](https://github.com/conll/reference-coreference-scorers/blob/f49f3f8a0e1cdc5ceba7c2a33013897369df5543/LICENSE) [Bundled modules](https://github.com/conll/reference-coreference-scorers/tree/f49f3f8a0e1cdc5ceba7c2a33013897369df5543/lib)

## Changes

Benchopedia preserves the original token values and order, displays each token beside its published index, and renders coreference annotations as JSON clusters of inclusive mention spans. It assigns stable keys derived from the CoNLL document IDs and links individual records to their original files. The four input files contain 1,584 distinct token sequences.

## Notices

The pinned MIT text is included alongside the task snapshot and reproduced here.

```text
MIT License

Copyright (c) 2020 Natural Language Processing @UCLA

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
