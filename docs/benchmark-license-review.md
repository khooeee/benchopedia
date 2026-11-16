# Benchmark redistribution review

Reviewed 2026-11-15 against default-branch commit `7668d30`. Scope: the three
benchmarks present at that commit, their pinned dataset cards, copied prompts
and solutions, and existing notices. Unmerged benchmark additions are outside
this review. This records upstream evidence and remaining work, rather than
certifying ownership of every question or code excerpt.

Each benchmark's current terms and required notices now live in
`data/<id>/redistribution-review.md`, which the build publishes as the License
section of its page. Article sections such as the methodology do not carry
license text. This file remains the record of the initial audit.

| Benchmark | Imported tasks | Finding |
| --- | ---: | --- |
| GSM8K | 1,319 | Redistribution allowed by the reviewed MIT license; its full notice is retained in its redistribution review and generated benchmark page. |
| MMLU | 14,042 | The pinned dataset card explicitly declares MIT and links to the project license. The import lacked the copyright and permission notice; this change adds it to the snapshot and benchmark page. This relies on the upstream license declaration, not an independent clearance of every source question. |
| SWE-bench Verified | 500 | Not cleared as currently packaged. The pinned card supplies no license declaration, and copied reference patches contain code from projects with different terms. Required notices and a task/file-level redistribution review are missing. |

## GSM8K

The snapshot is the original non-Socratic test split at
`3101c7d5072418e28b9008a6636bde82a006892c`. The
[upstream MIT license](https://github.com/openai/grade-school-math/blob/3101c7d5072418e28b9008a6636bde82a006892c/LICENSE)
permits copying and redistribution subject to retention of the copyright and
permission notice. The full OpenAI notice is in
[`redistribution-review.md`](../data/gsm8k/redistribution-review.md), which the
build publishes on the benchmark page. Prompts and solutions remain upstream text. No separate restriction was
found in the reviewed source.

## MMLU

The imported `all/test` split is pinned at
`c30699e8356da336a370243923dbaf21066bb9fe`. Its
[dataset card](https://huggingface.co/datasets/cais/mmlu/blob/c30699e8356da336a370243923dbaf21066bb9fe/README.md)
declares MIT in both its metadata and licensing section, linking to the original
[Dan Hendrycks MIT notice](https://github.com/hendrycks/test/blob/4450500f923c49f1fb1dd3d99108a0bd9717b660/LICENSE).
The card leaves its source-data collection and source-language-producer sections
unspecified. Thus the available evidence supports reuse under the publisher's
MIT declaration, but does not establish rights in each underlying source item.

This change preserves the upstream notice in [`data/mmlu/LICENSE`](../data/mmlu/LICENSE)
and reproduces it in [`redistribution-review.md`](../data/mmlu/redistribution-review.md)
for the generated website. It does
not change task text, answer mappings, counts, or the dataset revision. The
license review should be revisited if a source owner raises a conflicting claim.

## SWE-bench Verified: unresolved

A [deeper follow-up](research/swe-bench-redistribution.md) inventories root
licenses at all 499 source revisions and examines prompt provenance, including
Django Trac tickets. It finds no blanket redistribution ban, while keeping the
permission and packaging questions below open.

The [pinned dataset card](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified/blob/c104f840cc67f8b6eec6f759ebc8b2693d585d4a/README.md)
describes issue text and gold patches but contains neither a license field nor
a licensing section. The
[SWE-bench software repository's MIT license](https://github.com/SWE-bench/SWE-bench/blob/02e7a74ffd0b707aab73d203fe87bdc7c76afc8e/LICENSE)
is not sufficient evidence that all quoted issue text and third-party patch
code can be redistributed under MIT.

All 500 imported tasks were counted by their source repository. The following
licenses were read at one representative imported pull request's head revision
per repository. These are starting points for review, not clearance of every
patch or its potentially different file-level terms. Labels below reflect the
license text, including where GitHub's automatic classification was inconclusive.

| Source project | Imported tasks | Representative upstream license |
| --- | ---: | --- |
| astropy/astropy | 22 | [BSD-3-Clause](https://github.com/astropy/astropy/blob/efedd57cb088b6ca73f9540a3c6185ad7046c926/LICENSE.rst) |
| django/django | 231 | [BSD-3-Clause](https://github.com/django/django/blob/5e4d354e2dad0f2b4002d3e2eafe9ea8ca6a8a1f/LICENSE) |
| matplotlib/matplotlib | 34 | [Matplotlib license (retains notices; summarizes changes)](https://github.com/matplotlib/matplotlib/blob/a06f25e58dd453f8776b1cf411af5c371ff0789e/LICENSE/LICENSE) |
| mwaskom/seaborn | 2 | [BSD-3-Clause](https://github.com/mwaskom/seaborn/blob/e99a1e4b83f7e076b54942e5f8fde2364f2cd2e4/LICENSE.md) |
| pallets/flask | 1 | [BSD-3-Clause](https://github.com/pallets/flask/blob/b8b410014d85f9861acc87c5f21c9a55a42d09c9/LICENSE.rst) |
| psf/requests | 8 | [Apache-2.0 notice](https://github.com/psf/requests/blob/8d8865aadb9c76863820c87431229d20e5c23a70/LICENSE) |
| pydata/xarray | 22 | [Apache-2.0](https://github.com/pydata/xarray/blob/ad71bb2da711434989f872531c220c3bbe9374d5/LICENSE) |
| pylint-dev/pylint | 10 | [GPL version 2](https://github.com/pylint-dev/pylint/blob/194e6d35d40f15828bae97dccd4871d49537bdbc/LICENSE) |
| pytest-dev/pytest | 19 | [MIT](https://github.com/pytest-dev/pytest/blob/87265973218e37bf7839bfbbd25fe69f1fe50a15/LICENSE) |
| scikit-learn/scikit-learn | 32 | [BSD-3-Clause; file exceptions need review](https://github.com/scikit-learn/scikit-learn/blob/992fd6e962606e1c64ecd1ba4fd8147d3fd4a29a/COPYING) |
| sphinx-doc/sphinx | 44 | [BSD-2-Clause; bundled exceptions need review](https://github.com/sphinx-doc/sphinx/blob/e571479d5485e787c26497918a10801c12d9a98e/LICENSE) |
| sympy/sympy | 75 | [BSD-3-Clause](https://github.com/sympy/sympy/blob/af40819536a8e5facf941ceb4f742bcf4fa1f3f6/LICENSE) |

For example, `pylint-dev__pylint-4551` copies a patch to
[`pylint/pyreverse/diagrams.py`](https://github.com/pylint-dev/pylint/blob/194e6d35d40f15828bae97dccd4871d49537bdbc/pylint/pyreverse/diagrams.py),
whose header explicitly identifies GPL licensing and contributor copyrights.
GPL allows redistribution under its conditions; it is not a blanket copying
ban. The current Benchopedia snapshot does not preserve that license or those
notices. Similar attribution and notice obligations exist under permissive
licenses as well. The root Benchopedia MIT notice cannot replace them.

Before treating this import as cleared, map every copied patch to the applicable
project and file terms, retain required notices and license texts in both the
repository and published output, and establish the redistribution basis for
issue text separately. Resolve GPL source-distribution obligations and any
project-specific exceptions. If the obligations cannot be met, obtain permission
or agree on a reduced scope (for example, linking to reference patches rather
than copying them). Do not silently remove tasks or claim that a software
harness license clears the dataset.

This review leaves the existing SWE-bench task snapshot unchanged and explicitly
open for that follow-up; adding a license label alone would not resolve it.
Since 2026-11-15, Benchopedia excludes these tasks from the repository and the
website until they are cleared; see [`data/swe-bench-verified/exclusions.md`](../data/swe-bench-verified/exclusions.md).
