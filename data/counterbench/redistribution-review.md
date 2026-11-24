# CounterBench redistribution review

## Scope

Benchopedia publishes the causal-rule backgrounds, questions, and answer
labels from all 1,200 records in `data_balanced_alpha_V1.json` and
`data_balanced_backdoor_V2.json` at revision
`c6225dfa00b7a89ccfeae67797b9a6d80e48e44c`. The paper links this release
and describes generating the questions from causal graphs and templates
with artificial variable names.
[Pinned release](https://huggingface.co/datasets/CounterBench/CounterBench/tree/c6225dfa00b7a89ccfeae67797b9a6d80e48e44c) ·
[Original study, Section 2.2](https://arxiv.org/html/2502.11008v2#S2.SS2)

## Terms

The authors' pinned dataset card identifies the license for the release
as MIT. Both files are public and downloadable without an account or
approval. The license permits redistribution with attribution and its
permission notice.
[Pinned dataset card](https://huggingface.co/datasets/CounterBench/CounterBench/blob/c6225dfa00b7a89ccfeae67797b9a6d80e48e44c/README.md) ·
[MIT license text](https://spdx.org/licenses/MIT.html)

## Changes

Benchopedia combines each `given_info` and `question` with a paragraph
break. It preserves the released answer label and namespaces each
`question_id` by source file. The guide uses the released question-type
field for its breakdown.

## Notices

CounterBench by Yuefei Chen, Vivek K. Singh, Jing Ma, and Ruixiang Tang.
The upstream dataset card declares MIT. The standard MIT permission and
warranty text accompanies the snapshot.

```
MIT License

CounterBench dataset by Yuefei Chen, Vivek K. Singh, Jing Ma, and Ruixiang Tang.

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
