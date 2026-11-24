# NLGraph Maximum Flow redistribution review

## Scope

Benchopedia publishes the 150 Easy and 200 Hard standard maximum-flow inputs and references from the authors' repository at `a369f32341c16aaad9d84e7ab835aa3376df1cc3`. The inputs are generated directed graphs, integer capacities, and source and sink node IDs. The author evaluation script identifies these exact two standard directories and their record counts. [Easy files](https://github.com/Arthur-Heng/NLGraph/tree/a369f32341c16aaad9d84e7ab835aa3376df1cc3/NLGraph/flow/graph/easy/standard) [Hard files](https://github.com/Arthur-Heng/NLGraph/tree/a369f32341c16aaad9d84e7ab835aa3376df1cc3/NLGraph/flow/graph/hard/standard) [Original paper](https://arxiv.org/abs/2305.10037)

## Terms

The authors' pinned repository makes the generated graph data and the original evaluation format available under its MIT license. The selected files are available without authentication, a gate, or a separate data agreement. The terms permit public redistribution and modification with the copyright and permission notices preserved. [Pinned MIT license](https://github.com/Arthur-Heng/NLGraph/blob/a369f32341c16aaad9d84e7ab835aa3376df1cc3/LICENSE) [Dataset description](https://github.com/Arthur-Heng/NLGraph/blob/a369f32341c16aaad9d84e7ab835aa3376df1cc3/README.md)

## Changes

Benchopedia renders each raw file into the prose used by the original zero-shot formatter, preserves the graph's directed capacities and reference value, and derives a key from difficulty and filename. Its chat adapter requests and reads an integer reply. [Pinned formatter and evaluator](https://github.com/Arthur-Heng/NLGraph/blob/a369f32341c16aaad9d84e7ab835aa3376df1cc3/evaluation/flow.py)

## Notices

NLGraph was created by Heng Wang, Shangbin Feng, Tianxing He, Zhaoxuan Tan, Xiaochuang Han, and Yulia Tsvetkov. The MIT notice is reproduced here and in `LICENSE`. [Authors and citation](https://arxiv.org/abs/2305.10037)

```text
MIT License

Copyright (c) 2024 Heng Wang

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
