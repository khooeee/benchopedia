# HumanEval-X redistribution review

## Scope

The snapshot contains all 820 HumanEval-X problems in the five data files under codegeex/benchmark/humaneval-x at commit `2838420b7b4492cf3d16bce5320e26e65960c9e2` of zai-org/CodeGeeX: 164 each in Python, C++, Java, JavaScript, and Go. For each problem it includes the prompt, canonical solution, and test program, which are code with English comments. The Rust file, the CodeGeeX model code and weights, and the generation and translation scripts are not included. Both the public repository and the website publish this content. No images are copied. [Data folder](https://github.com/zai-org/CodeGeeX/tree/2838420b7b4492cf3d16bce5320e26e65960c9e2/codegeex/benchmark/humaneval-x)

## Terms

The data files sit in the CodeGeeX repository, whose LICENSE is the Apache License 2.0; a separate MODEL_LICENSE covers only the model weights. The dataset card for the earlier Hugging Face copy also declares Apache 2.0. Apache 2.0 permits copying, redistribution, and modified versions when a copy of the license is included, modified files carry notices that they were changed, and any NOTICE file is kept. The repository has no NOTICE file, and the license text is kept beside this review as LICENSE. The data has no access gate. [LICENSE](https://github.com/zai-org/CodeGeeX/blob/2838420b7b4492cf3d16bce5320e26e65960c9e2/LICENSE), [MODEL_LICENSE](https://github.com/zai-org/CodeGeeX/blob/2838420b7b4492cf3d16bce5320e26e65960c9e2/MODEL_LICENSE), and [Hugging Face dataset card](https://huggingface.co/datasets/zai-org/humaneval-x/blob/62c78627f3072a1454fa0cb0184737cafe5e4198/README.md)

The paper says the authors manually rewrote each HumanEval prompt, canonical solution, and test set in C++, Java, JavaScript, and Go. The Python files are HumanEval's own prompts and solutions, and the other languages translate them. HumanEval is distributed by OpenAI under the MIT license, which permits copying, modification, and redistribution, including in derived works, when its copyright and permission notice is kept. That notice is reproduced below. No other third-party content was found. [CodeGeeX paper](https://arxiv.org/abs/2303.17568) and [HumanEval license](https://github.com/openai/human-eval/blob/b9453e8f1865df0a0057a1383767caa400acfbcf/LICENSE)

## Changes

Benchopedia puts the upstream task ID and function name above each prompt and wraps the prompt in a fenced block. It assembles each solution from the prompt, canonical solution, and test program, builds IDs from the language and problem number, and adds source and environment links. Prompt, solution, and test text is unchanged.

The grader preserves the CodeGeeX prompt assembly, standard imports and generated-code cleanup from the pinned evaluator under the same Apache 2.0 license. The small per-problem context needed to reconstruct test programs is downloaded from the pinned files into the user's local build directory.

## Notices

HumanEval-X is from "CodeGeeX: A Pre-Trained Model for Code Generation with Multilingual Benchmarking on HumanEval-X" by Qinkai Zheng, Xiao Xia, Xu Zou, Yuxiao Dong, Shan Wang, Yufei Xue, Zihan Wang, Lei Shen, Andi Wang, Yang Li, Teng Su, Zhilin Yang, and Jie Tang. It is used under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0), kept in full beside this review as LICENSE.

HumanEval is from "Evaluating Large Language Models Trained on Code" by Mark Chen and coauthors. Its upstream notice is reproduced here.

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
