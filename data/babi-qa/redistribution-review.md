# bAbI QA redistribution review

## Scope

The repository and crawlable pages publish the story text, questions, and reference
answers for all 20,000 questions in the `en-10k` test split of bAbI QA v1.2.
The Facebook archive has SHA-256
`f7f0bee187efca0d81c3daac1b162cda4eb7f9505dee5ad6846eabbed3dbf92e`.
The input is generated text from the original Facebook AI Research benchmark.
[Archive](https://dl.fbaipublicfiles.com/parlai/babi/babi.tar.gz) ·
[ParlAI download manifest](https://github.com/facebookresearch/ParlAI/blob/a29567f7ce76992fd1f03c51ba9e3b155a37ea51/parlai/tasks/babi/build.py)

## Terms

The archive's `tasks_1-20_v1-2/LICENSE.txt` identifies Facebook, Inc. and
licenses the bAbI tasks data under Creative Commons Attribution 3.0 Unported.
The download is public and requires no account or approval. The license
permits sharing and adapting the data with attribution, preservation of the
copyright notice, and a link to its terms. The benchmark credits the paper's
authors and includes the original notice and legal text in `LICENSE.txt`.
[Facebook dataset card](https://huggingface.co/datasets/facebook/babi_qa/blob/021d7aeb7307b7856dd0632f92827bc607dc2f1b/README.md) ·
[CC BY 3.0 Unported legal code](https://creativecommons.org/licenses/by/3.0/legalcode) ·
[Original paper](https://arxiv.org/abs/1502.05698v10)

## Changes

Benchopedia splits each story into question-level records, joins the preceding
statements and the question in a prompt, and adds a deterministic task key.
It drops the line numbers and supporting-fact annotations. Story and question
wording and the stored reference labels come from the archive.

## Notices

Dataset by Jason Weston, Antoine Bordes, Sumit Chopra, Alexander M. Rush,
Bart van Merriënboer, Armand Joulin, and Tomas Mikolov, Facebook AI Research.

```
CC License

bAbI tasks data

Copyright (c) 2015-present, Facebook, Inc. All rights reserved.
```
