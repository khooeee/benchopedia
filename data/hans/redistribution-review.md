# HANS redistribution review

## Scope

Benchopedia publishes the premise, hypothesis, original pair ID and binary gold label for all 30,000 pairs from `heuristics_evaluation_set.txt`, at `7299f6f657089ce06a0f98e7e81f8d0f5b7741ce` with SHA-256 `c55b62feef9913070e88f38938dc2492018c945ac81f70139346472494124e79`. The paper describes the authors' construction of these sentence pairs from templates. The separate MultiNLI examples, training file and syntactic parse fields are outside the snapshot. [Pinned evaluation file](https://github.com/tommccoy1/hans/blob/7299f6f657089ce06a0f98e7e81f8d0f5b7741ce/heuristics_evaluation_set.txt) [Original paper](https://aclanthology.org/P19-1334/)

## Terms

The authors' repository identifies the evaluation set and distributes it under the MIT license. The file is available without authentication, gate approval or a separate data agreement. The license permits public sharing and adaptation with its copyright and permission notices retained. [Pinned repository instructions](https://github.com/tommccoy1/hans/blob/7299f6f657089ce06a0f98e7e81f8d0f5b7741ce/README.md) [Pinned MIT license](https://github.com/tommccoy1/hans/blob/7299f6f657089ce06a0f98e7e81f8d0f5b7741ce/LICENSE.md)

## Changes

Benchopedia keeps the original tokenized sentences and places them under Premise and Hypothesis labels. It uses each pair ID as its key and displays the original gold label. The reporting guide reads the heuristic, subcase and template directly from the source file.

## Notices

HANS was created by R. Thomas McCoy, Ellie Pavlick, and Tal Linzen. The original MIT notice is reproduced here and in `LICENSE`. [Authors and citation](https://aclanthology.org/P19-1334/)

```text
MIT License

Copyright (c) 2019 R. Thomas McCoy

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
