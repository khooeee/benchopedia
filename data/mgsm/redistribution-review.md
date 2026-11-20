# MGSM redistribution review

## Scope

The snapshot contains all 2,750 rows of the eleven MGSM language files at commit `452a21ad3dae5668c06ceeac21ff073e1e40f9be` of google-research/url-nlp: 250 problems and numeric answers in each of Bengali, Chinese, English, French, German, Japanese, Russian, Spanish, Swahili, Telugu, and Thai. The repository's evaluator includes the first six worked examples in each of the eleven languages from the pinned [exemplars.py](https://github.com/google-research/url-nlp/blob/452a21ad3dae5668c06ceeac21ff073e1e40f9be/mgsm/exemplars.py). Any local run record can show the selected examples in its model request. Both the public repository and the website publish the test problems and answers. No upstream evaluator code or images are copied. [Language files](https://github.com/google-research/url-nlp/tree/452a21ad3dae5668c06ceeac21ff073e1e40f9be/mgsm)

## Terms

The mgsm directory at the pinned commit contains the Creative Commons Attribution 4.0 International Public License. It permits copying, redistribution, public display, and adaptation when the work is credited, a link to the license is given, and changes are stated. It adds no non-commercial or share-alike condition. The license file was added in May 2024; the language files have not changed since they were published in October 2022. The directory has no access gate or separate restriction on publishing the problems. [License at the pinned commit](https://github.com/google-research/url-nlp/blob/452a21ad3dae5668c06ceeac21ff073e1e40f9be/mgsm/LICENSE) and [history of the mgsm directory](https://github.com/google-research/url-nlp/commits/452a21ad3dae5668c06ceeac21ff073e1e40f9be/mgsm)

The problems are translations of the first 250 GSM8K test problems, and the English file repeats those problems verbatim. GSM8K is distributed under the MIT license, whose notice is reproduced below. The paper states that paid professional translators produced the translations. [Original paper](https://arxiv.org/abs/2210.03057) and [GSM8K license](https://github.com/openai/grade-school-math/blob/3101c7d5072418e28b9008a6636bde82a006892c/LICENSE)

## Changes

Benchopedia converts each tab-separated row into a task record, assigns IDs from the language code and line number, and adds source links. Question and answer text is unchanged. The evaluator joins six worked examples with blank lines and uses their localized question and answer labels for the test question. The worked-example wording is unchanged.

## Notices

MGSM is from "Language Models are Multilingual Chain-of-Thought Reasoners" by Freda Shi, Mirac Suzgun, Markus Freitag, Xuezhi Wang, Suraj Srivats, Soroush Vosoughi, Hyung Won Chung, Yi Tay, Sebastian Ruder, Denny Zhou, Dipanjan Das, and Jason Wei, published in the google-research/url-nlp repository. It is used under the [Creative Commons Attribution 4.0 International license](https://creativecommons.org/licenses/by/4.0/). The full license text from the pinned commit accompanies this snapshot as LICENSE.

The English problems and the problems that MGSM translates come from GSM8K, whose notice is reproduced below.

```text
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
