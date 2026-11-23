# SimpleQA redistribution review

## Scope

The snapshot contains all 4,326 questions and reference answers in OpenAI's published SimpleQA test file, pinned by SHA-256 `feee3f7e7db3617e94e8fcf1977b756ec420ef8568f4e0fcbbe0e92e9d5fc032`. The file's metadata column, which holds topic tags and the annotators' supporting sources, is not included. Both the public repository and the website publish the questions and answers. The grader uses the upstream judge prompt. No images are copied. [Test file](https://openaipublic.blob.core.windows.net/simple-evals/simple_qa_test_set.csv)

## Terms

OpenAI's simple-evals README, at commit `652c89d0ca9df547706735883097e9537d40dc47`, lists SimpleQA among its benchmarks with a link to the repository's MIT license, and that license names OpenAI as copyright holder. The MIT license permits copying, redistribution, and public display when the copyright and permission notice is retained. The pinned evaluation code downloads the same test file. The paper describes the questions and answers as written by OpenAI's AI trainers and calls the benchmark open-sourced. The file has no access gate or separate restriction on publishing it. [README](https://github.com/openai/simple-evals/blob/652c89d0ca9df547706735883097e9537d40dc47/README.md), [license](https://github.com/openai/simple-evals/blob/652c89d0ca9df547706735883097e9537d40dc47/LICENSE), [evaluation code](https://github.com/openai/simple-evals/blob/652c89d0ca9df547706735883097e9537d40dc47/simpleqa_eval.py), and [paper](https://cdn.openai.com/papers/simpleqa.pdf)

The test file itself carries no license statement; this review relies on the README's declaration for SimpleQA. The supporting-source entries were left out because some contain text quoted from cited webpages, whose terms this declaration does not cover.

## Changes

Benchopedia converts each CSV row into a task record, assigns positional IDs, adds source links, and leaves out the metadata column. Question and answer text is unchanged. The grader prompt is copied from the pinned evaluation code under the same MIT notice.

## Notices

The upstream notice accompanies this snapshot as LICENSE and is reproduced below.

```text
MIT License

Copyright (c) 2024 OpenAI

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
