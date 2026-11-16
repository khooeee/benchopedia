# BIRD-SQL redistribution review

## Scope

The snapshot contains all 1,534 questions in the BIRD-SQL development split released on 2025-11-06, from the single data file at revision `3c11fb193e5439b338e23677fa0aae11e8b85db9` of the birdsql/bird_sql_dev_20251106 dataset. For each question it includes the question text, the database name, the evidence text, and the gold SQL query. Difficulty labels are not shown. The SQLite databases, their description files, the training split, and earlier development releases are not included. Both the public repository and the website publish this content. No code or images are copied. [Dataset files](https://huggingface.co/datasets/birdsql/bird_sql_dev_20251106/tree/3c11fb193e5439b338e23677fa0aae11e8b85db9)

## Terms

The dataset card at the pinned revision declares the Creative Commons Attribution-ShareAlike 4.0 International license. The BIRD repository README states that the authors changed the license to CC BY-SA 4.0, and the BIRD homepage dates that change to April 27, 2024. That license permits copying, redistribution, public display, and adaptation when the work is credited, a link to the license is given, changes are indicated, and adaptations are shared under the same terms. The dataset has no access gate. [Dataset card](https://huggingface.co/datasets/birdsql/bird_sql_dev_20251106/blob/3c11fb193e5439b338e23677fa0aae11e8b85db9/README.md), [repository README](https://github.com/AlibabaResearch/DAMO-ConvAI/blob/7635e3f7fd7136cddc462d7f184fd497d5bd5e4c/bird/README.md), [BIRD homepage](https://bird-bench.github.io/), and [legal code](https://creativecommons.org/licenses/by-sa/4.0/legalcode)

The paper says annotators hired by the authors wrote the questions and SQL, and expert annotators wrote the evidence sentences. The dataset card says the 2025-11-06 release was reviewed and revised by the BIRD team. The databases come from Kaggle, the CTU Prague Relational Learning Repository, and open tables, and they are not copied here. Questions and queries quote short values from those databases, such as school, player, and card names, one short phrase of card text, and a few Stack Exchange post titles and comment phrases from codebase_community; no longer passages of database text appear. [Original paper](https://arxiv.org/abs/2305.03111) and [dataset card](https://huggingface.co/datasets/birdsql/bird_sql_dev_20251106/blob/3c11fb193e5439b338e23677fa0aae11e8b85db9/README.md)

## Changes

Benchopedia assembles each prompt from the upstream question, a Database: line with the database name, and an Evidence: line with the evidence text, which is left out when the evidence is empty or only whitespace. It stores the gold SQL as the reference answer, builds IDs from the upstream question number, and adds source and setup links. Question, evidence, and SQL text is unchanged.

## Notices

BIRD is from "Can LLM Already Serve as A Database Interface? A BIg Bench for Large-Scale Database Grounded Text-to-SQLs" by Jinyang Li, Binyuan Hui, Ge Qu, Jiaxi Yang, Binhua Li, Bowen Li, Bailin Wang, Bowen Qin, Ruiying Geng, Nan Huo, Xuanhe Zhou, Chenhao Ma, Guoliang Li, Kevin C.C. Chang, Fei Huang, Reynold Cheng, and Yongbin Li. The 2025-11-06 development release is published by the BIRD team.

This material is shared under the [Creative Commons Attribution-ShareAlike 4.0 International license](https://creativecommons.org/licenses/by-sa/4.0/legalcode). Adaptations of these questions and queries must remain under those terms. Benchopedia's MIT license does not replace them.
