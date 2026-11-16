# BIG-Bench Extra Hard redistribution review

## Scope

This review covers all 4,520 input and target pairs at commit `80d12ca916b7158f22293fcf3144f4d3d854d4be`, for both the public repository and the website. The separate BBEH Mini subset is not included.

## Terms

The official dataset is publicly downloadable without an access gate. Its README explicitly licenses non-software materials under CC BY 4.0, which permits redistribution with attribution, a license link, and disclosure of changes. This relies on the publisher’s dataset license declaration, including the adapted task materials, rather than the separate software license. [Upstream license and disclaimer](https://github.com/google-deepmind/bbeh/blob/80d12ca916b7158f22293fcf3144f4d3d854d4be/README.md#license-and-disclaimer)

## Changes

Benchopedia converts the JSON example arrays to JSONL, assigns stable positional keys, and adds source links. Input and target text are unchanged.

## Notices

Copyright 2025 Google LLC. BBEH data and other non-software materials are distributed under [Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/); upstream software is Apache 2.0. The materials are provided on an AS IS basis, without warranties or conditions of any kind. This is not an official Google product.

The accompanying ATTRIBUTION.md retains the upstream citations and license notice. Credit for the full benchmark goes to [Kazemi and coauthors](https://arxiv.org/abs/2502.19187); the upstream authors also request attribution to the prior work behind its task groups. [Upstream citations](https://github.com/google-deepmind/bbeh/blob/80d12ca916b7158f22293fcf3144f4d3d854d4be/README.md#citing-this-work)

These include [BoardgameQA](https://arxiv.org/abs/2306.07934); [MoCa](https://proceedings.neurips.cc/paper_files/paper/2023/hash/f751c6f8bfb52c60f43942896fe65904-Abstract-Conference.html); [Causal reasoning and large language models](https://arxiv.org/abs/2305.00050); [LLMs cannot find reasoning errors, but can correct them!](https://arxiv.org/abs/2311.08516); [GeomVerse](https://arxiv.org/abs/2312.12241); [Linguini](https://arxiv.org/abs/2409.12126); [Do Androids Laugh at Electric Sheep?](https://arxiv.org/abs/2209.06293); [Humor in AI](https://arxiv.org/abs/2406.10522); [Spatial understanding](https://arxiv.org/abs/2310.14540); [SportQA](https://arxiv.org/abs/2402.15862); [SARC](https://aclanthology.org/L18-1102/); [Test of Time](https://arxiv.org/abs/2406.09170); [LiveBench](https://arxiv.org/abs/2406.19314); [Causal language modeling for logic puzzles](https://arxiv.org/abs/2409.10502).
