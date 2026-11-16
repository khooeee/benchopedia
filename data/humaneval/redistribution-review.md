# HumanEval redistribution review

## Scope

This review covers all 164 original tasks, HumanEval/0 through HumanEval/163, at revision `b9453e8f1865df0a0057a1383767caa400acfbcf`: prompts, canonical solutions, and tests. Both the public repository and the website publish them. The example problem and sample files are not imported. Rerunning the importer at this revision reproduces the snapshot exactly. [Pinned data](https://github.com/openai/human-eval/blob/b9453e8f1865df0a0057a1383767caa400acfbcf/data/HumanEval.jsonl.gz)

## Terms

Cleared for both the repository and the website, provided the MIT notice is retained.

The dataset file is distributed in the upstream repository, whose only license is MIT, copyright OpenAI. The repository has no separate data license, NOTICE file, or usage terms in its README, and it is public without an access gate. MIT permits copying, publishing, and distribution when the copyright and permission notice is retained. [Upstream license](https://github.com/openai/human-eval/blob/b9453e8f1865df0a0057a1383767caa400acfbcf/LICENSE) and [README](https://github.com/openai/human-eval/blob/b9453e8f1865df0a0057a1383767caa400acfbcf/README.md)

The paper states that all problems were hand-written by the authors and not programmatically copied from existing sources, and that OpenAI released the dataset in that repository for others to evaluate with. The dataset card in OpenAI’s Hugging Face organization also declares MIT and identifies OpenAI as the curator. No third-party content was found that the MIT grant would not cover. [Paper, section 2.2](https://arxiv.org/abs/2107.03374) and [dataset card](https://huggingface.co/datasets/openai/openai_humaneval/blob/7dce6050a7d6d172f3cc5c32aa97f52fa1a2e544/README.md)

Since 2026-10-16, the README marks the repository as deprecated and unmaintained, provided for historical reference. That notice does not change the license.

## Changes

Benchopedia adds a heading and code fence to each prompt, and assembles each solution from the upstream prompt, canonical solution, and tests, as described in the methodology. The upstream text is unchanged.

## Notices

The upstream README asks users to cite the paper: Mark Chen and coauthors, [Evaluating Large Language Models Trained on Code](https://arxiv.org/abs/2107.03374), 2021. The original upstream notice is reproduced here.

```text
The MIT License

Copyright (c) OpenAI (https://openai.com)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
```
