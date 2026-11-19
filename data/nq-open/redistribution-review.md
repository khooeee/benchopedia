# NQ-Open redistribution review

## Scope

The snapshot contains the complete original NQ-Open development split: all
3,610 lines of `nq_open/NQ-open.dev.jsonl` at commit
`fb26a3073b1fe636c97302890a27b491d6530130` of
google-research-datasets/natural-questions. Each line is an English question and
its reference answers. The training split and the EfficientQA development and
test splits in the same folder are not imported. Both the public repository and
the website publish this content. It is text only, with no images, passages, or
code from the dataset.
[Dataset folder](https://github.com/google-research-datasets/natural-questions/tree/fb26a3073b1fe636c97302890a27b491d6530130/nq_open)

The benchmark's `eval.py` also contains three short functions copied from the
ORQA evaluation utilities in google-research/language at commit
`865fae65f63ef7e6b2989d4ff8b47f61750415a8`, which Benchopedia's runner uses to
grade model answers the way the official scorer does.
[Evaluation utilities](https://github.com/google-research/language/blob/865fae65f63ef7e6b2989d4ff8b47f61750415a8/language/orqa/utils/eval_utils.py)

## Terms

The NQ-Open README at the pinned commit states: "All of the Natural Questions
data is released under the CC BY-SA 3.0 license", linking to the Creative
Commons Attribution-ShareAlike 3.0 license. Google's own copy of the split on
Hugging Face declares the same license. The repository's `LICENSE` file is the
Apache License 2.0, which covers its code; the data statement above is the grant
for the questions and answers. The files are a plain download from GitHub, with
no account, form, or click-through terms.
[NQ-Open README](https://github.com/google-research-datasets/natural-questions/blob/fb26a3073b1fe636c97302890a27b491d6530130/nq_open/README.md)
and [Hugging Face card](https://huggingface.co/datasets/google-research-datasets/nq_open/blob/5dd9790a83002ad084ddeb7c420dc716852c6f28/README.md)

CC BY-SA 3.0 permits copying, distributing, and adapting the work, including
commercially, provided that the work is credited as its licensor asks, the
license or its address accompanies every copy, the licensor's notices are kept,
an adaptation is identified as such, and adaptations are shared under the same
or a compatible license. The README asks users to cite Kwiatkowski et al. (2019)
and Lee et al. (2019). Benchopedia credits both below, links the license, and
offers its adapted snapshot under CC BY-SA 3.0. Benchopedia's MIT license does
not apply to this material.
[CC BY-SA 3.0 legal code](https://creativecommons.org/licenses/by-sa/3.0/legalcode)

The questions are queries that several users issued to Google search, which the
Natural Questions authors describe as "real anonymized, aggregated queries".
The answers are short spans that annotators marked on English Wikipedia pages;
Lee et al. kept only answers of at most five tokens, such as names, dates, and
numbers. The snapshot contains no Wikipedia passages. The split does not record
which page each answer came from, so Benchopedia cannot credit individual
articles; this review relies on Google's CC BY-SA 3.0 release of the answers and
on their being short factual phrases rather than passages of article text. A
scan of the imported text found no email addresses, telephone numbers, or URLs.
[Natural Questions paper](https://aclanthology.org/Q19-1026/) and
[ORQA paper](https://arxiv.org/abs/1906.00300)

The three functions in `eval.py` are Copyright 2018 The Google AI Language Team
Authors and licensed under the Apache License 2.0, which permits redistribution
when recipients receive a copy of the license and the copyright notice is kept.
The license text is kept beside this review as `LICENSE-language`, and
`eval.py` names the source file, its copyright, and its license.
[google-research/language LICENSE](https://github.com/google-research/language/blob/865fae65f63ef7e6b2989d4ff8b47f61750415a8/LICENSE)

## Changes

Benchopedia uses each question unchanged as the task prompt and lists the
question's reference answers as the solution, one per line in the upstream
order. Keys are `dev-` and the question's line number, which the file does not
record. Source links point to that line of the pinned file. Question and answer
text is otherwise unchanged.

`eval.py` copies `normalize_answer`, `exact_match_score`, and
`metric_max_over_ground_truths` unchanged, and adds an answer-format instruction
for chat models and the extraction of the answer from their final line.

## Notices

NQ-Open is from "Latent Retrieval for Weakly Supervised Open Domain Question
Answering" by Kenton Lee, Ming-Wei Chang, and Kristina Toutanova (ACL 2019), and
its questions and answers are from "Natural Questions: A Benchmark for Question
Answering Research" by Tom Kwiatkowski, Jennimaria Palomaki, Olivia Redfield,
Michael Collins, Ankur Parikh, Chris Alberti, Danielle Epstein, Illia
Polosukhin, Jacob Devlin, Kenton Lee, Kristina Toutanova, Llion Jones, Matthew
Kelcey, Ming-Wei Chang, Andrew M. Dai, Jakob Uszkoreit, Quoc Le, and Slav Petrov
(TACL 2019). The data is published by Google.

This snapshot is an adaptation of the NQ-Open development split, shared under
the [Creative Commons Attribution-ShareAlike 3.0 Unported license](https://creativecommons.org/licenses/by-sa/3.0/legalcode),
as the original is. Adaptations of it must remain under those terms.

The notice on the ORQA evaluation code copied into `eval.py`:

```text
Copyright 2018 The Google AI Language Team Authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

NQ-Open carries no canary string.
