# MATH redistribution review

## Scope

The snapshot contains all 5,000 test problems and worked solutions from the EleutherAI/hendrycks_math mirror at revision `21a5633873b6a120296cce3e2df9d5550074f4a3`: algebra (1,187), counting and probability (474), geometry (479), intermediate algebra (903), number theory (540), prealgebra (871), and precalculus (546). Training problems and the separate AMPS pretraining set are not included. Both the public repository and the website publish the test problems and solutions. [Dataset card](https://huggingface.co/datasets/EleutherAI/hendrycks_math/blob/21a5633873b6a120296cce3e2df9d5550074f4a3/README.md)

## Terms

The pinned dataset card declares MIT and identifies the dataset as the MATH dataset from the authors' repository. That repository distributes its materials under the MIT notice reproduced below. The card does not identify or clear each underlying contest problem. The available evidence supports reuse under those MIT declarations, but does not establish rights in each source problem. [Upstream notice](https://github.com/hendrycks/math/blob/985bdc1696e88e8643f081a0ff4719da39f2ae2a/LICENSE) and [dataset card](https://huggingface.co/datasets/EleutherAI/hendrycks_math/blob/21a5633873b6a120296cce3e2df9d5550074f4a3/README.md)

The problems are not in the authors' git repository. The README at `357963a7f5501a6c1708cf3f3fb0cdf525642761` links to an author-hosted archive that returned no file when this snapshot was reviewed. The current README links to a third-party copy that merges problems into one split. This import uses the pinned mirror instead of either of those. [Earlier download link](https://github.com/hendrycks/math/blob/357963a7f5501a6c1708cf3f3fb0cdf525642761/README.md) and [current download link](https://github.com/hendrycks/math/blob/985bdc1696e88e8643f081a0ff4719da39f2ae2a/README.md)

## Changes

Benchopedia assigns subject-and-row IDs and adds source links. Problem and solution text is unchanged. Difficulty labels are checked and then left out of the task record. The Benchopedia evaluator includes the authors' boxed-answer extraction and equivalence helpers from their MIT-licensed repository at the pinned code revision. The functions retain the upstream logic. [Box extraction](https://github.com/hendrycks/math/blob/985bdc1696e88e8643f081a0ff4719da39f2ae2a/modeling/dataset/util.py), [box removal](https://github.com/hendrycks/math/blob/985bdc1696e88e8643f081a0ff4719da39f2ae2a/modeling/eval_math_gpt.py), and [equivalence](https://github.com/hendrycks/math/blob/985bdc1696e88e8643f081a0ff4719da39f2ae2a/modeling/math_equivalence.py)

## Notices

The authors' notice is preserved with this snapshot as LICENSE and reproduced below.

```text
MIT License

Copyright (c) 2021 Dan Hendrycks

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
