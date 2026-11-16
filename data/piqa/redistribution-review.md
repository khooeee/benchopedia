# PIQA redistribution review

Reviewed on 2026-11-16 for repository commit `21edab439af693b961be2f069e8690a88d3b4e37`, validation split only.

## Source

- Publisher: Yonatan Bisk, Rowan Zellers, Ronan Le Bras, Jianfeng Gao, and Yejin Choi
- Source checked: https://github.com/ybisk/ybisk.github.io/tree/21edab439af693b961be2f069e8690a88d3b4e37/piqa/data
- Files: `valid.jsonl` (495,929 bytes, 1,838 rows) and `valid-labels.lst` (3,676 bytes, 1,838 labels)
- Introduced: 2019-11-26, arXiv:1911.11641
- Project page: https://yonatanbisk.com/piqa/

## Distribution terms

The data notes and the project page both name the Academic Free License ("AFL") v. 3.0: https://opensource.org/license/afl-3-0

The grant of copyright permission includes reproducing the work, distributing or communicating copies to the public, and displaying the work publicly. It does not add a non-commercial or share-alike condition. That covers publication in this public git repository and on the crawlable website.

The same grant requires that notices present in the source be kept. The data notes link the license and do not include a separate copyright line. This review attributes the authors and links the license rather than inventing a notice.

## Scope

`valid.jsonl` has 1,838 goals with two solutions each, and `valid-labels.lst` has 1,838 labels, each `0` or `1`. This import keeps all 1,838. Twenty-seven goals occur more than once, always with different solutions or labels. None of those rows is dropped.

`train.jsonl` has 16,113 examples and is training material. `tests.jsonl` has 3,084 examples, the same two fields, and no label file. Those files are not imported.

## Changes

- The goal is stored as the question, followed by the two solutions numbered `1.` and `2.`.
- The stored answer is the one-based solution number and its text. Upstream label `0` selects the first solution and `1` selects the second.
- The goal and both solution strings are otherwise unchanged. No row in this split uses a carriage return.
- The source has no example IDs. IDs are `piqa-0001` through `piqa-1838` in the pinned file order.

## Notices

PIQA: Reasoning about Physical Commonsense in Natural Language. Yonatan Bisk, Rowan Zellers, Ronan Le Bras, Jianfeng Gao, and Yejin Choi. https://yonatanbisk.com/piqa/

The data notes state: License Academic Free License ("AFL") v. 3.0.
