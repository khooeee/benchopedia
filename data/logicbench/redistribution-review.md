# LogicBench redistribution review

## Scope

This review covers the public LogicBench(Eval) binary question-answering split
at `c014153303c98de4d5f09d41c3a235cd869be5c8`. It covers the natural-language
contexts, question variants, binary labels, source IDs, and rule names in the
25 released BQA files. The repository and website display these fields as
task inputs, source links, and reference labels. [Pinned source directory](https://github.com/Mihir3009/LogicBench/tree/c014153303c98de4d5f09d41c3a235cd869be5c8/data/LogicBench%28Eval%29/BQA)

## Terms

The authors explicitly release LogicBench data under the MIT License. The
pinned GitHub source directory is publicly accessible without sign-in or a
click-through agreement. The release documentation and paper describe the
contexts and questions as template- and model-generated material validated by
its authors. The data release names no third-party text or media dependency for
these fields. The grant permits copying, modification, publication, and
redistribution with the original notices. [Pinned data release](https://github.com/Mihir3009/LogicBench/blob/c014153303c98de4d5f09d41c3a235cd869be5c8/README.md#data-release) [Data creation](https://arxiv.org/html/2404.15522v2#S3.SS2) [MIT license](https://github.com/Mihir3009/LogicBench/blob/c014153303c98de4d5f09d41c3a235cd869be5c8/LICENSE)

## Changes

Benchopedia converts each released question variant to a separate JSONL row,
assigns a key using the logic family, rule directory, sample ID, and question
position, adds context and question labels, and attaches pinned source links.
The original context and question text are retained. The grader writes its own
instructions and follows the metric definitions and reply format in the paper.

## Notices

Data by Mihir Parmar, Nisarg Patel, Neeraj Varshney, Mutsumi Nakamura, Man Luo,
Santosh Mashetty, Arindam Mitra, and Chitta Baral. [LogicBench paper](https://aclanthology.org/2024.acl-long.739/)

The complete upstream notice is reproduced below and in this directory's license file.

```
MIT License

Copyright (c) 2024 Mihir

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
