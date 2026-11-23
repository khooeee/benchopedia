# miniF2F redistribution review

## Scope

The snapshot contains the 488 Lean theorem statements in `lean/src/test.lean` and `lean/src/valid.lean` at commit `e4f113090ad82d64f8ce064d2f55b613a9b6bded` of facebookresearch/miniF2F, 244 per split, together with the complete tactic proofs the files supply for 164 of them. It is Lean source text only: no natural-language problem statements, no images, and no files for the other proof assistants. The repository's `informal` directory is reviewed below and is not imported. Both the public repository and the website publish this content. [Lean statements at the imported revision](https://github.com/facebookresearch/miniF2F/tree/e4f113090ad82d64f8ce064d2f55b613a9b6bded/lean/src)

## Terms

The repository releases each proof assistant's material under terms matching that assistant's main library, and states that "the `lean` folder is released under the Apache License". `lean/LICENSE` holds the Apache License 2.0 text, identical to the canonical text, and every Lean source file repeats the grant in its header. The paper states the same split of terms: the Metamath version under the MIT License, the Lean and Isabelle versions under the Apache License. Apache 2.0 permits copying, redistribution, and modified versions when a copy of the license is included, the copyright, patent, trademark, and attribution notices are kept, and modified files carry notices that they were changed. The license text is kept beside this review as `LICENSE`. The repository's top-level `LICENSE` is the MIT License of Meta Platforms, Inc., kept beside this review as `LICENSE-repository`. Nothing is access-gated, and no part of the repository asks that the statements be withheld from publication. [Repository README](https://github.com/facebookresearch/miniF2F/blob/e4f113090ad82d64f8ce064d2f55b613a9b6bded/README.md), [lean/LICENSE](https://github.com/facebookresearch/miniF2F/blob/e4f113090ad82d64f8ce064d2f55b613a9b6bded/lean/LICENSE), and [Paper](https://arxiv.org/abs/2109.00110)

The imported statements are formalizations written by the benchmark's authors, not the wording of the contests and textbooks the problems come from. A statement names its source problem, such as `imo_1960_p2` or `mathd_algebra_478`, and then expresses it in Lean's syntax with mathlib's definitions; no AMC, AIME, IMO, or MATH problem text is published here. The grant above covers these formalizations and the proofs. It does not establish rights in each underlying competition or textbook problem, and the files record no terms for those sources.

The repository's `informal` directory, which pairs every problem with a natural-language statement and proof, is excluded. Its README names three sources for that text: the MATH dataset, the Art of Problem Solving website, and manual annotation by named contributors. The per-problem JSON records do not say which source each field came from, and several fields still carry Art of Problem Solving wiki markup such as `[[logarithm]]`, so the text cannot be attributed to its rights holders item by item. The top-level MIT notice is the repository's own and does not stand in for permission from those third parties, which is the same gap recorded for other declined candidates. The formal statements are unaffected: they are the authors' own Lean source. [informal directory at the imported revision](https://github.com/facebookresearch/miniF2F/tree/e4f113090ad82d64f8ce064d2f55b613a9b6bded/informal) and [informal component paper](https://arxiv.org/abs/2210.12283)

## Changes

Benchopedia does not publish a modified copy of the Lean files. It extracts each `theorem` declaration and splits it at `begin`: the statement becomes the task prompt, shown under a heading naming the split and problem and inside a fenced block, and the declaration with its proof becomes the reference solution. Lean text is copied verbatim; nothing is reformatted, renamed, or corrected. IDs combine the split and the upstream problem name. Source links point at the declaration's lines in its split file at the pinned commit, and the environment link points at `leanpkg.toml`. The file preamble of imports and notation, the helper lemma `sum_pairs`, the scripts, and the material for the other proof assistants are not imported, and declarations whose proof contains `sorry` are published without a reference solution.

The grader also incorporates the upstream test file's standalone `sum_pairs` helper lemma under Apache 2.0. The lemma's text is unchanged and the benchmark's license remains alongside the grader. [Helper source](https://github.com/facebookresearch/miniF2F/blob/e4f113090ad82d64f8ce064d2f55b613a9b6bded/lean/src/test.lean#L1613)

## Notices

miniF2F is from "miniF2F: a cross-system benchmark for formal Olympiad-level mathematics" by Kunhao Zheng, Jesse Michael Han, and Stanislas Polu. The Lean statements and proofs are used under the [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0), kept in full beside this review as `LICENSE`.

The header of `lean/src/test.lean`, reproduced verbatim:

```
/-
Copyright (c) 2021 OpenAI. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Kunhao Zheng, Kudzo Ahegbebu, Stanislas Polu, David Renshaw, OpenAI GPT-f
-/
```

The header of `lean/src/valid.lean`, reproduced verbatim:

```
/-
Copyright (c) 2021 OpenAI. All rights reserved.
Released under Apache 2.0 license as described in the file LICENSE.
Authors: Kunhao Zheng, Stanislas Polu, David Renshaw, OpenAI GPT-f
-/
```

The repository's top-level notice, reproduced verbatim and kept in full beside this review as `LICENSE-repository`:

```
MIT License

Copyright (c) Meta Platforms, Inc. and affiliates.
```

Benchopedia's MIT license does not replace the terms above.
