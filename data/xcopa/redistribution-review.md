# XCOPA redistribution review

## Scope

The snapshot contains the complete XCOPA test sets: all 500 records in each of
the eleven files `data/<language>/test.<language>.jsonl` at commit
`e2e9d7f105a758ee869cd13e0fe251ef93a29840` of cambridgeltl/xcopa, 5,500 in all, for Estonian, Haitian Creole,
Indonesian, Italian, Southern Quechua, Swahili, Tamil, Thai, Turkish,
Vietnamese, and Mandarin Chinese. For each record it includes the translated
premise, the two translated alternatives, the direction, and the label. The
validation sets, the machine-translated English files in `data-gmt`, and the
README's baseline figure are not copied. Both the public repository and the
website publish this content. It is text only, with no code or images.
[Data at the pinned commit](https://github.com/cambridgeltl/xcopa/tree/e2e9d7f105a758ee869cd13e0fe251ef93a29840/data)

## Terms

The repository's `LICENSE.md` at the pinned commit is the full text of the
Creative Commons Attribution 4.0 International Public License, and GitHub
identifies the repository's license as CC-BY-4.0. The file was added on
2020-04-27, before the dataset's first release, and the data files were last
changed by the pinned commit on 2021-02-04. The license permits copying,
redistribution, public display, and adaptation when the work is credited, a
link to the license is given, and changes are indicated. It adds no
non-commercial or share-alike condition. The data are downloaded directly from
GitHub with no form, account, or click-through terms. The README asks users of
the data to cite both the XCOPA paper and the original COPA paper; both are
credited below.
[License at the pinned commit](https://github.com/cambridgeltl/xcopa/blob/e2e9d7f105a758ee869cd13e0fe251ef93a29840/LICENSE.md),
[history of the license file](https://github.com/cambridgeltl/xcopa/commits/e2e9d7f105a758ee869cd13e0fe251ef93a29840/LICENSE.md),
and [README](https://github.com/cambridgeltl/xcopa/blob/e2e9d7f105a758ee869cd13e0fe251ef93a29840/README.md)

Every record translates a COPA question. COPA's publisher distributes COPA
under the BSD 2-Clause License, which permits redistribution with or without
modification when its copyright notice, conditions, and disclaimer are kept;
Benchopedia's COPA review records the evidence for that license. The notice is
reproduced below. According to the paper, one native speaker per language made
the translations; the README credits the Quechua translation to Irma Alvarez
Ccoscco and names no other translators.
[COPA project page, archived 2024-04-02](https://web.archive.org/web/20240402061922/https://people.ict.usc.edu/~gordon/copa.html)
and [paper](https://aclanthology.org/2020.emnlp-main.185/)

A scan of the imported text found no contact details, web addresses, or other
personal data.

## Changes

Benchopedia builds each task prompt from the translated premise, an English
question for the record's direction, and the two translated alternatives,
numbered and labelled as on Benchopedia's COPA page. XCOPA records the direction
as the English word `cause` or `effect`, so the question is COPA's English
wording, "What was the CAUSE of this?" or "What happened as a RESULT?". The
translated sentences are reproduced exactly as published. In 346 records the
direction disagrees with the COPA question being translated; the snapshot keeps
the published direction and the benchmark page describes the discrepancy.

The reference solution is the labelled alternative with its number. The
`changed` field, which marks the 132 records whose label is the translators'
majority answer rather than the individual translator's, and the numeric
`idx` field are not copied as fields. Keys combine the language code with
`idx`, and source links point at the record's line in the pinned file.

## Notices

XCOPA is from "XCOPA: A Multilingual Dataset for Causal Commonsense Reasoning"
by Edoardo M. Ponti, Goran Glavaš, Olga Majewska, Qianchu Liu, Ivan Vulić, and
Anna Korhonen, Proceedings of the 2020 Conference on Empirical Methods in
Natural Language Processing (EMNLP), published in the cambridgeltl/xcopa
repository. The Quechua translation is by Irma Alvarez Ccoscco. XCOPA is used
under the [Creative Commons Attribution 4.0 International
license](https://creativecommons.org/licenses/by/4.0/), whose full text from the
pinned commit accompanies this snapshot as `LICENSE`.

The questions XCOPA translates are from COPA, "Choice of Plausible
Alternatives: An Evaluation of Commonsense Causal Reasoning" by Melissa
Roemmele, Cosmin Adrian Bejan, and Andrew S. Gordon, AAAI Spring Symposium on
Logical Formalizations of Commonsense Reasoning, 2011. COPA's license, as
published on its project page:

```
Copyright (c) 2010, University of Southern California
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

* Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

* Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
```

XCOPA carries no canary string.
