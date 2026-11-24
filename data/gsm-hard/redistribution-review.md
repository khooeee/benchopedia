# GSM-Hard redistribution review

## Scope

Benchopedia publishes the problem text and numeric targets for all 1,319
entries in `gsmhardv2.jsonl` at revision
`960448f73503112d4226baeb8eb41d3fb5ae2506`. These entries adapt GSM8K
test questions by changing quantities and recalculating their answers.
[Pinned dataset](https://huggingface.co/datasets/reasoning-machines/gsm-hard/blob/960448f73503112d4226baeb8eb41d3fb5ae2506/gsmhardv2.jsonl) ·
[PAL paper](https://proceedings.mlr.press/v202/gao23f.html)

## Terms

The authors' Hugging Face release declares MIT for the dataset and makes the
file available without sign-in. The source GSM8K questions are also under
MIT. Both grants permit redistribution with attribution and the copyright
and permission notices.
[Pinned GSM-Hard dataset card](https://huggingface.co/datasets/reasoning-machines/gsm-hard/blob/960448f73503112d4226baeb8eb41d3fb5ae2506/README.md) ·
[GSM8K source license](https://github.com/openai/grade-school-math/blob/3101c7d5072418e28b9008a6636bde82a006892c/LICENSE)

## Changes

Benchopedia assigns line-number keys and records the published target as a
decimal string. The snapshot publishes the `input` and `target` fields
from each entry. The published program field is outside this snapshot.

## Notices

GSM-Hard by Luyu Gao, Aman Madaan, Shuyan Zhou, Uri Alon, Pengfei Liu,
Yiming Yang, Jamie Callan, and Graham Neubig. The authors identify the
dataset's license as MIT.

The original GSM8K permission notice is included in `LICENSE-GSM8K` and
reproduced below.

```
MIT License

Copyright (c) 2021 OpenAI

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
