# PCFG SET Systematicity and Productivity redistribution review

## Scope

Benchopedia publishes all 10,175 systematicity pairs and 11,333 productivity pairs from the authors' naturalized PCFG SET release at `4f75bdd78889150dd78e90bbb7ddec840204c159`. The four source files are the `test.src` and `test.tgt` files for those two tests. They contain generated string-edit expressions and their output sequences. The paper and release describe the grammar and construction of these files. [Pinned data release](https://github.com/i-machine-think/am-i-compositional/tree/4f75bdd78889150dd78e90bbb7ddec840204c159/data/pcfgset) [Original paper](https://arxiv.org/abs/1908.08351)

## Terms

The authors' repository distributes the test files under its MIT license. The selected files are accessible without authentication, approval or a separate data agreement. The grant permits redistribution and modification with the copyright and permission notices preserved. A separate generator repository documents the string-edit operations. Benchopedia credits that source in the benchmark and uses its own plain-language instructions. [Pinned MIT license](https://github.com/i-machine-think/am-i-compositional/blob/4f75bdd78889150dd78e90bbb7ddec840204c159/LICENSE) [Operation definitions](https://github.com/MathijsMul/pcfg-set/blob/99098bd97150671003de60526d884d7c24949944/tasks/default.py)

## Changes

Benchopedia pairs the input and answer lines as JSON records and adds stable keys from the split and original one-based line number. The expressions and targets are preserved verbatim apart from removal of the line terminators. The 2,891 pairs shared across the two tests keep each split's original occurrence. The evaluator adds descriptions of the operations to the model prompt.

## Notices

PCFG SET was created by Dieuwke Hupkes, Verna Dankers, Mathijs Mul, and Elia Bruni. The authors' MIT notice appears below and beside the snapshot in `LICENSE`. [Authors and citation](https://arxiv.org/abs/1908.08351)

```text
MIT License

Copyright (c) 2020 i-machine-think

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
