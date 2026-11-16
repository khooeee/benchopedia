# SWE-bench Verified redistribution research

Reviewed 2026-11-15. This follows the [initial review](../benchmark-license-review.md)
and concerns Benchopedia's existing 500-task snapshot, not SWE-bench Pro,
Multilingual, Multimodal, or later revisions.

## Finding

**No blanket ban on redistributing this snapshot was found in the reviewed
primary sources. The source-code licenses allow redistribution under conditions.
The current Benchopedia packaging still needs work before it can be called
cleared.** Missing notices are a concrete gap; permission for all prompt text,
especially Django's Trac tickets, remains a question requiring clarification.

The initial review treated the MIT license as evidence about the software alone.
Historical packaging provides additional evidence of intent to distribute data:
the official repository [contained Verified parquet data](https://github.com/SWE-bench/SWE-bench/tree/9fa561428aeef6406f534c8370c670f9ce51c630/data/SWE-bench_Verified)
alongside an [MIT license](https://github.com/SWE-bench/SWE-bench/blob/9fa561428aeef6406f534c8370c670f9ce51c630/LICENSE).
That supports a broader reading of the publisher's intent. It does not establish
that the publisher can replace third-party licenses, or expressly confirm terms
for the exact older Hugging Face snapshot used here.

## What was checked

The imported dataset is `princeton-nlp/SWE-bench_Verified`, revision
`c104f840cc67f8b6eec6f759ebc8b2693d585d4a`, test split. Its
[pinned card](https://huggingface.co/datasets/princeton-nlp/SWE-bench_Verified/blob/c104f840cc67f8b6eec6f759ebc8b2693d585d4a/README.md)
contains no license declaration and no restriction on public mirroring was found
there. The Hugging Face API reported it public and ungated at that revision.
Public access alone is not the redistribution grant.

The review compared all 500 local prompts and reference patches with that
upstream dataset; all matched exactly. The dataset revision was checked before
and after reading its rows. It then retrieved each source project's root license
at all 499 distinct `base_commit` revisions represented by those tasks. All
retrievals succeeded, producing 37 distinct license texts. The
[license inventory](swe-bench-license-inventory.csv) records their SHA-256 hashes,
task counts, revision counts, and immutable example URLs. Counts cover all 500
tasks; two Django tasks share a base revision.

This is a complete baseline-root-license inventory, not a complete rights audit
of every file, quoted snippet, ticket, or added line at its eventual merge
revision. The CSV gives one example URL per distinct text, not every task's
provenance. Local research evidence also retains the full revision mapping.
The imported JSONL's SHA-256 was
`06840d8ef0484756039b94870fd2172632283032f5992bc15e8cbc9b123421bf`.

## The rights are in several layers

| Material | Evidence and implication |
| --- | --- |
| SWE-bench's own code and dataset arrangement | The official README describes code and data, its repository carries MIT, and earlier packaging included Verified data. This supports redistribution intent for the authors' own contribution. The pinned dataset card leaves the exact dataset grant unstated. |
| Reference patch code | Original project and file terms continue to matter. All reviewed root-license families permit redistribution, with differing notice and other conditions. |
| GitHub issue text | GitHub's contribution-license provision supplies a possible basis under the source repository's license, subject to its scope, historical applicability, separate agreements, and the contributor's authority. |
| Django ticket text | The collector reads Trac, not GitHub issues. GitHub's repository-contribution provision does not itself settle rights in these tickets. |
| Linked Dockerfiles and environments | Benchopedia currently links to these instead of copying the files or distributing container images. Research about their licensing does not automatically block linking. |

The [original paper, section 8 and Table 12](https://arxiv.org/html/2310.06770v3)
recognizes the underlying repository licenses and says its collection complies
with them. This supports following those terms, rather than treating every
record as wholly authored and freely relicensable by the benchmark authors.
Its statement that licenses permit noncommercial use is not a new
noncommercial-only license; the actual license texts govern.

## Reference patches: redistribution is possible, with obligations

| Source-project terms | Tasks | Work needed for redistribution |
| --- | ---: | --- |
| BSD-family defaults, including Sphinx and SymPy exceptions | 407 | Preserve applicable copyright notices, conditions, and disclaimers. Review bundled/file-specific exceptions and contributor attribution. |
| MIT: pytest | 19 | Include the upstream copyright and permission notice. |
| Apache-2.0: Requests and xarray | 30 | Include the full license, retain relevant notices, check any applicable NOTICE file, and mark modifications when required. |
| Matplotlib's custom license | 34 | Retain its license and copyright notices; its derivative-work clause also calls for a brief summary of changes. |
| GPL-family: Pylint | 10 | Preserve the applicable GPL grant, copyright and warranty notices, and comply with conditions for any modified work. Do not offer the copied code as MIT-only. |

The [initial review's source table](../benchmark-license-review.md#swe-bench-verified-unresolved)
links the twelve projects' representative license files. The new inventory
extends that evidence to every imported base revision. The 37 variants include
changed copyright years and supplemental notices; one current root license per
project would miss those differences. Sphinx and SymPy's root files also contain
third-party sections, so their short labels alone are insufficient.

[Apache-2.0 section 4](https://www.apache.org/licenses/LICENSE-2.0#redistribution)
sets out license, notice, and modification obligations. For Matplotlib, the
[reviewed license](https://github.com/matplotlib/matplotlib/blob/a06f25e58dd453f8776b1cf411af5c371ff0789e/LICENSE/LICENSE)
expressly permits reproduction, public display, derivative works, and distribution
subject to its conditions. Neither is a general prohibition on Benchopedia.

### Pylint and GPL

All ten Pylint base revisions contained the same GPL version 2 text. The patches
contain 21 file/revision pairs: 20 Python source pairs and one `setup.cfg`.
Every Python pair's base-file header (or added-file text, where applicable)
identified GPL licensing; one header appeared after 45 lines of copyrights.
Package metadata in one patch also says `GPL-2.0-or-later`, so an implementation
should preserve the applicable grant instead of inferring an "only" restriction
from the root license text alone. An
[example source header](https://github.com/pylint-dev/pylint/blob/194e6d35d40f15828bae97dccd4871d49537bdbc/pylint/pyreverse/diagrams.py)
confirms this is third-party GPL code, not simply benchmark-authored answer text.

[GPLv2 sections 1 and 2](https://opensource.org/license/gpl-2.0)
allow source redistribution under conditions. Section 2 also distinguishes an
independent work aggregated with GPL material from a derivative work. Thus
including separately identified GPL examples does not automatically require
relicensing Benchopedia's independent viewer under GPL. This is an application
of the aggregation provision, not a determination of the legal boundary of
this particular website.

Benchopedia publishes patch source text, not a compiled Pylint executable.
Section 3's object-code distribution requirements should not be assumed to apply
merely because a website displays a patch. A compliant design should nevertheless
provide the preferred editable patch form, identify its source and changes, and
include the relevant notices and license alongside it. The exact requirements
for the selected packaging should be settled before claiming compliance.

## Prompt text: the main unresolved permission question

For non-Django projects, the
[official collector](https://github.com/SWE-bench/SWE-bench/blob/02e7a74ffd0b707aab73d203fe87bdc7c76afc8e/swebench/collect/utils.py#L251)
combines resolved GitHub issues' titles and bodies. It keeps hints separately;
Benchopedia imports the problem statement, not `hints_text`.

[GitHub's current terms, D.5 and D.6](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service#d-user-generated-content)
distinguish platform permissions from contributions under a repository license.
D.6 provides a plausible repository-license basis for a contributor's own issue
text. It does not establish authority over third-party quotations, override a
separate agreement, or resolve the applicable terms for every older submission.
This is stronger evidence than public availability, but requires provenance.

Nine imported tasks have PR creation dates before 2017-03-01. GitHub's
[February 28, 2017 announcement](https://github.blog/2017-02-28-new-github-terms-of-service-are-in-effect/)
discusses the clarified contributor-license section. The nine dates are a reason
to inspect historical terms, not proof those tasks are unlicensed. Original
issues may predate their PRs, and later acceptance may also matter; this review
does not declare all later tasks cleared by current terms.

### Django: 231 prompts came through Trac collection

The collector has a
[Django-specific branch](https://github.com/SWE-bench/SWE-bench/blob/02e7a74ffd0b707aab73d203fe87bdc7c76afc8e/swebench/collect/utils.py#L353)
that reads ticket titles and descriptions from `code.djangoproject.com`. For
example, the prompt for `django__django-10097` comes from
[ticket 29528](https://code.djangoproject.com/ticket/29528), while Benchopedia's
source link points to the [associated PR](https://github.com/django/django/pull/10097).
The PR and ticket are different authored texts.

The same Trac branch is present in the [v2.1.7 collector](https://github.com/SWE-bench/SWE-bench/blob/5f5a7df799663adba4b191eca3d675faf3621fe2/swebench/collect/utils.py).
The task count covers all Django records; direct comparison with a live ticket
was a representative check, not a scrape and clearance of all 231 tickets.

Django's [tracker homepage](https://code.djangoproject.com/) identifies Django's
BSD license, and its [CLA FAQ](https://www.djangoproject.com/foundation/cla/faq/)
describes licensing contributions. These support an open contribution model,
but the reviewed sources did not establish a blanket grant for every ticket
reporter and every quoted reproduction example. The CLA is optional, so its
existence cannot establish that each reporter signed it. A GitHub login to Trac
also does not turn a ticket into a GitHub repository contribution.

The specific question for the Django Software Foundation or SWE-bench authors
is which grant covers republication of those full ticket descriptions in a
separate public archive, and which notices must accompany them. This remains
unresolved, rather than being a discovered prohibition.

## What Benchopedia currently distributes

Since 2026-11-15, Benchopedia excludes these tasks entirely; see
[`data/exclusions.json`](../../data/exclusions.json). This section describes the
packaging at the time of the research.

The repository copies full prompts and patches into `tasks.jsonl`. The build
publishes prompts on task pages and in its search JSON, and embeds patches in
task-page HTML under a disclosure control. Collapsing that control does not
remove the copied patch. PR/source links provide provenance but do not reproduce
all required copyright, license, and disclaimer notices. There is currently no
SWE-bench source-project notice bundle in either the snapshot or generated site.

The linked `swe-bench-tasks` repository has a separate open
[licensing-clarification issue](https://github.com/SWE-bench/swe-bench-tasks/issues/25).
It concerns generator/tooling licensing and is not evidence that the Verified
prompts or patches are prohibited. Do not copy those tools or images on the
assumption that the harness's MIT license automatically covers them.

## Recommended path

1. Ask the SWE-bench authors to confirm the grant for the exact pinned dataset,
   explicitly distinguishing their dataset arrangement from third-party issue
   text and code. For Django, confirm the applicable Trac-content terms or obtain
   an appropriate permission statement; do not assume a maintainer can grant
   rights owned only by individual reporters.
2. If that basis is established, create per-task provenance linking the original
   ticket/issue, PR, relevant code revision, applicable licenses, and notices.
   Preserve all needed license versions, relevant file-level notices, and
   attribution in both the Git distribution and generated website. Include
   visible license links wherever the copied material is served.
3. Keep third-party code under its own terms and make source patches available
   in an editable form. Review the GPL aggregation and modification conditions
   for the final packaging. No change to Benchopedia's original MIT code is
   automatically implied just by the presence of a GPL example.
4. If full-text rights remain unclear, agree on linking or original summaries
   for the affected content instead of silently removing records. Omitting
   patches alone does not resolve prompt permissions. Article-only entries need
   deliberate schema/UI support, since the present model requires tasks.

Do not rely on educational intent or noncommercial operation alone. The
[U.S. Copyright Office](https://www.copyright.gov/fair-use/) describes fair use as
a fact-specific balance; it is not blanket permission to mirror a whole dataset.
This research identifies evidence, a feasible compliance direction, and the
questions still open. It does not change the published dataset or certify that
every item is cleared. No permission requests were sent to upstream maintainers.
