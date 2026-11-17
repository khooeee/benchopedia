# SocialIQA redistribution review

Reviewed on 2026-11-16 for SocialIQA version 1.4, the test split only.

## Source

- Publisher: Maarten Sap, Hannah Rashkin, Derek Chen, Ronan LeBras, and Yejin Choi
- Source checked: https://maartensap.com/social-iqa/data/socialIQa_v1.4.tgz
- Archive checksum: SHA-256 `99a399d50f1a996388e94ab435ba0ceadc6b8ad9d90e6420358c962a4850d217` (2,391,426 bytes)
- Project page: https://maartensap.com/social-iqa/
- Introduced: 2019-04-22, arXiv:1904.09728

The GitHub repository linked from the project page did not resolve. The archive on the project page is the dataset, and its checksum is the revision recorded in `benchmark.json`.

## Distribution terms

The archive includes `LICENCE-CC-BY-4.txt`. That file is the Creative Commons Attribution 4.0 International legal text. It allows copying, redistribution, and public display when the authors, the title, and the source are credited and changes are stated. It does not add a non-commercial or share-alike condition.

The project page does not add a further access condition.

## Scope

`socialIQa_v1.4_tst.jsonl` has 2,224 examples. Every example has `context`, `question`, `answerA`, `answerB`, `answerC`, and `correct` of `A`, `B`, or `C`. This import keeps all 2,224. Twenty-one rows exactly repeat another row. None is dropped.

`socialIQa_v1.4_trn.jsonl` has 33,410 training examples. `socialIQa_v1.4_dev.jsonl` has 1,954 development examples. The separate archive `socialIQa_v1.4_withDims.tgz` is not imported.

## Changes

- The context and question are stored as the prompt, followed by the three answers labeled `A.`, `B.`, and `C.`.
- The stored answer is the reference letter and the text of the answer it selects.
- The context, question, and answer strings are otherwise unchanged. No row in this split uses a carriage return.
- The source has no example IDs. IDs are `socialiqa-0001` through `socialiqa-2224` in the pinned test-file order.

## Notices

SocialIQA: Commonsense Reasoning about Social Interactions. Maarten Sap, Hannah Rashkin, Derek Chen, Ronan LeBras, and Yejin Choi. https://maartensap.com/social-iqa/

The archive contains the Creative Commons Attribution 4.0 International legal text in `LICENCE-CC-BY-4.txt`.
