# MMLU-Pro redistribution review

Reviewed 2026-11-15 for adding the full 12,032-question test split to both the
public Benchopedia Git repository and crawlable website. No MMLU-Pro task file
was downloaded, imported, committed, or published during this review.

## Decision

The import remains on hold under the [required redistribution review](../adding-a-benchmark.md#required-redistribution-review).
The publisher explicitly declares MIT licensing for MMLU-Pro, including in its
paper. However, the paper also says that its four source collections retain
their own terms. Its description of the STEM Website source as “Open-Licensed”
does not identify those terms or the notices needed for republication. The
source website could not be inspected because it returned HTTP 403.

Before importing the complete split, establish the STEMEZ redistribution terms
and obligations applicable to the included material, or obtain authoritative
permission covering public repository and website republication. Preserve all
required notices with the snapshot and on the generated website. User approval
alone cannot supply rights held by a third party.

Do not silently exclude STEMEZ items or substitute a smaller split. An original
article with upstream links would require an explicit scope change and support
for article-only entries in the current schema.

## Exact proposed snapshot and access conditions

- Dataset: `TIGER-Lab/MMLU-Pro`, configuration `default`, split `test`.
- Dataset revision: `b189ec765aa7ed75c8acfea42df31fdae71f97be`.
- Proposed source file: `data/test-00000-of-00001.parquet`.
- Declared test count: 12,032; exclude the 70 validation examples.
- [Pinned dataset card](https://huggingface.co/datasets/TIGER-Lab/MMLU-Pro/blob/b189ec765aa7ed75c8acfea42df31fdae71f97be/README.md)
  declares `license: mit`, describes the source collections, and lists these counts.
- The [dataset metadata endpoint](https://huggingface.co/api/datasets/TIGER-Lab/MMLU-Pro)
  returned `private: false`, `gated: false`, and `disabled: false` when reviewed.
  This describes accessibility; it does not replace a redistribution license.

The intended imported content is question text, ordered answer options, and the
reference answer letter and text. Evaluation code, validation demonstrations,
and `cot_content` explanations are outside this proposed scope. Avoid copying
any task content until the outstanding permission issue is resolved.

## Publisher declarations

The [paper, version 6, Appendix A.5](https://arxiv.org/html/2406.01574v6#A1.SS5)
explicitly declares MIT licensing for MMLU-Pro. It separately identifies MMLU,
TheoremQA, and SciBench as MIT-licensed, and describes the STEM Website source
as “Open-Licensed.” It states that the four sources have their own terms.

[Section 3.2](https://arxiv.org/html/2406.01574v6#S3.SS2) identifies that website
as [STEMEZ](https://stemez.com/subjects). The paper describes converting questions
and solutions to multiple-choice items and generating additional distractors.
The dataset card similarly identifies all four source collections.

The separate [evaluation repository license](https://github.com/TIGER-AI-Lab/MMLU-Pro/blob/f418b116db00b065c2aea046518d8fcf74d39872/LICENSE)
is Apache 2.0. It should not be substituted for the dataset's MIT declaration.
No evaluation code was copied during this review.

## Source collections and notices reviewed

| Collection | Evidence | Remaining packaging or permission work |
| --- | --- | --- |
| MMLU | [MIT notice, Copyright 2020 Dan Hendrycks](https://github.com/hendrycks/test/blob/4450500f923c49f1fb1dd3d99108a0bd9717b660/LICENSE); the existing [Benchopedia review](../benchmark-license-review.md#mmlu) records reliance on the dataset publisher's MIT declaration. | Retain the applicable notice with the derived questions and published pages. |
| TheoremQA | [MIT notice, Copyright 2024 TIGER Lab](https://github.com/TIGER-AI-Lab/TheoremQA/blob/acfc9686aa9b49f3c8f189364a9a9ee9c53da039/LICENSE). | Retain the notice and record the relationship between the source collection and imported MMLU-Pro revision. |
| SciBench | [MIT notice, Copyright 2023 Xiaoxuan Wang](https://github.com/mandyyyyii/scibench/blob/e14e0ca3d3db0f02928a18d435b9c3d15656a7c5/LICENSE). Its [README](https://github.com/mandyyyyii/scibench/blob/e14e0ca3d3db0f02928a18d435b9c3d15656a7c5/README.md) describes textbook-derived questions. | Retain applicable notices and establish any additional terms for incorporated third-party material. |
| STEMEZ | The MMLU-Pro paper identifies the source and describes it as open-licensed. Requests to the HTTPS homepage and subjects page, and HTTP homepage, returned HTTP 403. | Obtain the actual applicable license or permission, including attribution and other conditions; reconcile it with the publisher's MIT declaration. |

The reviewed evidence contains no specific blanket prohibition on redistribution
of MMLU-Pro. The unresolved point is identifying and satisfying the underlying
source terms for the full proposed public import. A generic license label or
accessibility statement does not describe the missing source obligations.

## Conditions for resuming implementation

1. Document the applicable STEMEZ license or rights-holder permission and any
   additional terms on the incorporated source material. Confirm both public
   Git distribution and crawlable website publication are covered.
2. Keep the dataset at an immutable revision and preserve all required license
   texts, notices, attribution, and change descriptions in both publication forms.
3. Import every record in the declared test split, retaining question IDs,
   original option order, variable option counts, and correct answer mappings.
   Reject incomplete records and mismatched answer letters and indices.
4. Verify source links, deterministic re-import, data checks, all generated task
   routes, and local search and filtering before opening an implementation PR.

No benchmark metadata, importer, task snapshot, schema, or website behavior is
changed by this review. Future implementation should recheck upstream terms if
its revision, split, or publication scope changes.
