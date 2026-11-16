# MMLU redistribution review

## Scope

The snapshot contains all 14,042 questions, answer choices, and reference answers in the cais/mmlu all configuration, test split, at revision `c30699e8356da336a370243923dbaf21066bb9fe`. Both the public repository and the website publish them. [Dataset card](https://huggingface.co/datasets/cais/mmlu/blob/c30699e8356da336a370243923dbaf21066bb9fe/README.md)

## Terms

The pinned dataset card declares MIT in both its metadata and licensing section, and links to the original project license. The card leaves its source-data collection and source-language-producer sections unspecified. The available evidence therefore supports reuse under the publisher’s MIT declaration, but does not establish rights in each underlying source question. [Upstream license](https://github.com/hendrycks/test/blob/4450500f923c49f1fb1dd3d99108a0bd9717b660/LICENSE) and [initial review](https://github.com/khooeee/benchopedia/blob/main/docs/benchmark-license-review.md#mmlu)

## Changes

Question text and choices are unchanged. Prompts are assembled with labeled choices, and answer indices are converted to letters, as described in the methodology.

## Notices

The copyright and permission notice is preserved with this snapshot as LICENSE and reproduced below.

```text
MIT License

Copyright (c) 2020 Dan Hendrycks

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
