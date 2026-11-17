# DS-1000 redistribution review

## Scope

The snapshot contains all 1,000 DS-1000 problems in test.jsonl at revision `4416080ac5cb80bdf7576aefb8f9a0b4d5426a44` of the xlangai/DS-1000 dataset, which matches data/ds1000.jsonl.gz at commit `b39aab71da6d23ef8d3cac59a7c5f834516ab334` of xlang-ai/DS-1000. For each problem it includes the prompt and the reference solution, which contain prose and Python code. The test code in each problem's code_context, the cached model answers, and the original-format release are not included. Both the public repository and the website publish this content. No images are copied. [Dataset files](https://huggingface.co/datasets/xlangai/DS-1000/tree/4416080ac5cb80bdf7576aefb8f9a0b4d5426a44) and [repository](https://github.com/xlang-ai/DS-1000/tree/b39aab71da6d23ef8d3cac59a7c5f834516ab334)

## Terms

The repository's LICENSE file at the pinned commit is the Creative Commons Attribution-ShareAlike 4.0 International license, and the dataset card at the pinned revision declares the same license. It permits copying, redistribution, public display, and adaptation when the work is credited, a link to the license is given, notices are kept, changes are indicated, and adaptations are shared under the same terms. The dataset has no access gate. The license text is kept beside this review as LICENSE. [LICENSE](https://github.com/xlang-ai/DS-1000/blob/b39aab71da6d23ef8d3cac59a7c5f834516ab334/LICENSE) and [dataset card](https://huggingface.co/datasets/xlangai/DS-1000/blob/4416080ac5cb80bdf7576aefb8f9a0b4d5426a44/README.md)

The paper says the problems were adapted from Stack Overflow questions and the reference solutions from high-vote answers, then rewritten and perturbed by the authors. Stack Overflow distributes user contributions under CC BY-SA 2.5, 3.0, or 4.0, depending on when they were posted. Each of those versions allows adaptations to be shared under a later version with the same terms, so publishing DS-1000 under CC BY-SA 4.0 is consistent with them. DS-1000 does not record which Stack Overflow question each problem came from or who wrote it. This snapshot therefore keeps the attribution supplied with DS-1000 and credits Stack Overflow contributors as a group; it cannot name the original askers and answerers individually. [Original paper](https://arxiv.org/abs/2211.11501) and [Stack Overflow licensing](https://stackoverflow.com/help/licensing)

## Changes

Benchopedia puts a heading built from the upstream library, problem number, and perturbation metadata above each prompt and wraps the prompt in a fenced block for display. It stores the reference code as the reference answer, builds IDs from the upstream problem number, and adds source and environment links. Prompt and reference text is unchanged.

## Notices

DS-1000 is from "DS-1000: A Natural and Reliable Benchmark for Data Science Code Generation" by Yuhang Lai, Chengxi Li, Yiming Wang, Tianyi Zhang, Ruiqi Zhong, Luke Zettlemoyer, Scott Wen-tau Yih, Daniel Fried, Sida Wang, and Tao Yu. The simplified format was prepared by Yuhang Lai and Sida Wang. The problems are adapted from questions and answers by Stack Overflow contributors.

This material is shared under the [Creative Commons Attribution-ShareAlike 4.0 International license](https://creativecommons.org/licenses/by-sa/4.0/legalcode). Adaptations of these problems and solutions must remain under those terms. Benchopedia's MIT license does not replace them.
