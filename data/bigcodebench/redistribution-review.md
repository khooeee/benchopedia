# BigCodeBench redistribution review

## Scope

The snapshot contains all 1,140 tasks in the v0.1.4 split of bigcode/bigcodebench at revision `b74c0d0bf70d2c0bc459be537895cca163007f1a`: both prompt formats, the canonical solutions, and the unit test code for every task. Earlier version splits and the separate Hard subset are not included. Both the public repository and the website publish this content. The tasks contain Python code written for the benchmark; no third-party project source files or images are copied. [Dataset file](https://huggingface.co/datasets/bigcode/bigcodebench/blob/b74c0d0bf70d2c0bc459be537895cca163007f1a/data/v0.1.4-00000-of-00001.parquet)

## Terms

The pinned dataset card declares Apache 2.0. The paper's datasheet states that the dataset is distributed under Apache 2.0, and the evaluation harness repository ships the Apache License 2.0 text. Apache 2.0 permits reproduction, redistribution, and public display when recipients receive a copy of the license and modified files carry notices of the changes. Neither the dataset nor the harness has a NOTICE file. The dataset has no access gate or separate restriction on publishing the tasks. [Dataset card](https://huggingface.co/datasets/bigcode/bigcodebench/blob/b74c0d0bf70d2c0bc459be537895cca163007f1a/README.md), [original paper](https://arxiv.org/abs/2406.15877), and [license text](https://github.com/bigcode-project/bigcodebench/blob/09dd993f46c3fbf3a799465bb96d524edcb0b199/LICENSE)

The card says GPT-4 generated the tasks from seed examples in ODEX, which pairs intents with code from Stack Overflow, and that the tasks were then annotated by people. The paper describes the tasks as constructed from scratch, with the seeds used as starting points, and reports at most 0.09% 10-gram overlap between its task descriptions and ODEX intents. On this evidence the seeds are not reproduced in the tasks, and this review relies on the publisher's Apache 2.0 declaration. It does not independently clear every seed. [Original paper](https://arxiv.org/abs/2406.15877)

## Changes

Benchopedia shows both prompt formats on one task page under added headings and fences, assembles the reference solution with its tests in the order the harness runs them, assigns IDs, and adds source and environment links. Prompt, solution, and test text is unchanged.

## Notices

BigCodeBench is from "BigCodeBench: Benchmarking Code Generation with Diverse Function Calls and Complex Instructions" by Terry Yue Zhuo and coauthors, created by the BigCode Project and published on Hugging Face as bigcode/bigcodebench. It is used under the Apache License, Version 2.0. The full license text from the evaluation harness at commit `09dd993f46c3fbf3a799465bb96d524edcb0b199` accompanies this snapshot as LICENSE.
