# CommonsenseQA redistribution review

## Scope

The snapshot contains all 1,221 questions, choices, and reference answers in the random-split validation set of tau/commonsense_qa at revision `94630fe30dad47192a8546eb75f094926d47e155`. The training split is excluded. The 1,140-question leaderboard test split is excluded because that file publishes no reference answers. Both the public repository and the website publish this validation split. [Dataset card](https://huggingface.co/datasets/tau/commonsense_qa/blob/94630fe30dad47192a8546eb75f094926d47e155/README.md)

## Terms

The dataset author stated that the dataset is released under the MIT license. The authors' repository contains no LICENSE file and no copyright notice. The pinned dataset card repeats that statement and points at the same comment. No access gate was found. [Author's statement](https://github.com/jonathanherzig/commonsenseqa/issues/5#issuecomment-698754925)

## Changes

Question and choice text is unchanged. Prompts are assembled with labels A through E, and the reference answer is stored as its label plus the matching choice text. The ConceptNet concept field is not copied into the task record.

## Notices

The author's statement was:

```text
Hi,
Our dataset is licensed under an MIT license.

Best,
Jonathan
```

No upstream copyright or permission notice was published with the repository to reproduce beyond that statement.
