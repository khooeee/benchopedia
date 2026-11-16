# WinoGrande redistribution review

Reviewed on 2026-11-16 for WinoGrande version 1.1, the development split only.

## Source

- Publisher: Allen Institute for AI (Keisuke Sakaguchi, Ronan Le Bras, Chandra Bhagavatula, and Yejin Choi)
- Source checked: the public data package at https://storage.googleapis.com/ai2-mosaic/public/winogrande/winogrande_1.1.zip
- Package checksum: SHA-256 `3619ab104d8be2977b25c90ff420cb42d491707dcc75362a1e5d22bc082b7318` (3,395,492 bytes)
- Download pointer: `scripts/download_winogrande.sh` at repository commit `727e837f77521ef38bcc56df3b275c8da43f45af` fetches that URL
- Package README: `winogrande_1.1/README.md` inside the same zip
- Introduced: 2019-07-24, arXiv:1907.10641

The repository commit does not contain the questions. The zip is the dataset, and its checksum is the revision recorded in `benchmark.json`.

## Distribution terms

The README inside the data package says:

> License
>
> Winogrande dataset is licensed under CC BY 2.0.

That is Creative Commons Attribution 2.0, https://creativecommons.org/licenses/by/2.0/legalcode. It allows copying and redistribution, including on a public website, when the publisher, the title, and the source are credited and changes are stated. It does not add a non-commercial or share-alike condition.

The repository README at the same commit says the codebase is under the Apache License 2.0 and "The dataset is licensed under CC-BY." It does not name the version. The data package, which is the dataset itself, names CC BY 2.0. This import follows the package.

## Scope

The package development file `dev.jsonl` has 1,267 questions, and `dev-labels.lst` has 1,267 labels. Every embedded `answer` matches the label on the same line. Every question has a `qID`, a sentence, and two options. This import keeps all 1,267.

`test.jsonl` has no labels. The training files (`train_xs`, `train_s`, `train_m`, `train_l`, `train_xl`, and `train_debiased`) are training material, and the smaller files are reduced training subsets. None of those files is imported.

## Changes

- The sentence is stored as the question, followed by the two options numbered `1.` and `2.`.
- The stored answer is the matching option number and its text.
- The sentence and both option strings are otherwise unchanged. No question in this split uses a carriage return.
- Records are written in `qID` order. The label check uses the original line order before that sort.

## Notices

Winogrande dataset is licensed under CC BY 2.0.

WinoGrande: An Adversarial Winograd Schema Challenge at Scale. Keisuke Sakaguchi, Ronan Le Bras, Chandra Bhagavatula, and Yejin Choi. Allen Institute for AI. https://github.com/allenai/winogrande

The codebase is separately under the Apache License 2.0, with "Copyright Allen Institute for Artificial Intelligence" in that repository's LICENSE file. This import does not copy the codebase.
