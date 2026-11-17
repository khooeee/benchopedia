# BillSum redistribution review

## Scope

The snapshot contains the complete official US test split of BillSum: the 3,269
bills of `us_test_data_final_OFFICIAL.jsonl` inside the published archive
`billsum_v3.zip`, pinned by its SHA-256 digest
`5a55dfb231618d63b25cec4773280a2986d38f53d6d4d39b8256b278edf1110c`, with the
title, the full text, and the reference summary of each bill. The 18,949-bill
training split and the 1,237-bill California test split in the same archive are
not imported. Both the public repository and the website publish this content. It
is text only: no code, images, or test data are copied.
[Published archive](https://drive.usercontent.google.com/download?id=1g89WgFHMRbr4QrvA0ngh26PY081Nv3lx&export=download&confirm=t)
and [data documentation naming it](https://github.com/FiscalNote/BillSum/blob/master/BillSum_Data_Documentation.md)

The archive is a public Google Drive file. Drive answers a download of a file
this large with a virus-scan warning page, "Google Drive can't scan this file for
viruses", and the importer passes the confirmation parameter that page's own form
uses. No account, registration, or credential is involved, and no access
condition is bypassed. The repository's other download link, the one under
"Accessing the Dataset", returns a Google sign-in page instead; it is not used.
[Repository README](https://github.com/FiscalNote/BillSum/blob/master/README.md)

## Terms

Both halves of every task are works of the United States Government, which US
copyright law excludes from protection. The bill texts were collected from
govinfo, the United States Government Publishing Office's service, whose policies
page quotes 17 U.S.C. 105, "Copyright protection under this title is not
available for any work of the United States Government", and states "By virtue of
the foregoing, public documents can generally be reprinted without legal
restriction". The same page states that the intent of that section "is to place
in the public domain all work of the United States Government, which is defined
in 17 U.S.C. § 101 as work prepared by an officer or employee of the United
States Government as part of the person's official duties". The reference
summaries are, as Congress.gov describes its Summary tab, "bill summaries
authored by Legislative Analysts in the Congressional Research Service", a
department of the Library of Congress, so they are work of that kind.
[govinfo policies](https://www.govinfo.gov/about/policies),
[17 U.S.C. 105](https://www.law.cornell.edu/uscode/text/17/105), and
[Congress.gov, archived 2021-02-25](https://web.archive.org/web/20210225033348/https://www.congress.gov/legislation/about)

The publishers state the same conclusion for the collection. The dataset card in
FiscalNote's own Hugging Face repository declares CC0 1.0 for BillSum and records
that "The US bills were collected from the Govinfo service provided by the United
States Government Publishing Office (GPO) under CC0-1.0 license". The card's
narrative Licensing Information section is left as "More Information Needed", and
the authors' Kaggle copy of the dataset shows no terms at all, so the declaration
in the card metadata is the publishers' only statement; the status of the
underlying texts does not depend on it. The GitHub repository carries no terms of
its own and gates nothing.
[Dataset card at `3d8510441c06a3d9dfb32eb0d7f80151730bcc4f`](https://huggingface.co/datasets/FiscalNote/billsum/blob/3d8510441c06a3d9dfb32eb0d7f80151730bcc4f/README.md)

Two points remain noted rather than resolved. The govinfo policies page warns
that a government publication can contain third-party copyrighted material,
which "Publication in a Government document does not authorize any use or
appropriation of"; the imported documents are the legislative text of bills and
the analysts' summaries of them, and a scan found no copyright notice claimed by
anyone in them, though eighteen bills discuss copyright law as their subject. The
California test split is excluded partly for this reason as well: its summaries
are written by California's Legislative Counsel rather than a federal body, and
no equivalent statement covers them.

A scan of the imported text found no contact details or personal identifiers
beyond what Congress published in the bills themselves: a government contract
number, a toll-free Federal Communications Commission number printed in a
consumer notice, and two private relief bills that name the individual they would
benefit, each of which is part of the public legislative record of a bill
introduced in Congress.

## Changes

Benchopedia assembles each task prompt from one line asking for a summary of the
bill and quoting its official title, a line naming the bill and the Congress that
received it, and the bill text. The title, text, and summary are reproduced
exactly as published, with their original line breaks and indentation, including
the doubled quotation marks the legislative typesetter uses around amended
language and the stray control characters eleven records carry; those characters
are kept rather than repaired, which a browser renders as nothing or, for the one
null character in the split, as a replacement character. The bill text is
placed in a `~~~` fenced block, because those quotation marks are written as
pairs of backticks, which the prompt renderer would otherwise read as formatting;
no bill text contains that fence. The line naming the bill is derived from the upstream identifier, so
`106_hr2724` is written as `H.R. 2724, 106th Congress`.

The reference solution is the summary as published, unchanged. Keys are the
upstream bill identifiers. The upstream file records no per-bill address, so the
prompt and solution links of every task point at the published archive the text
came from, as the importer verified it.

## Notices

BillSum is from "BillSum: A Corpus for Automatic Summarization of US Legislation"
by Anastassia Kornilova and Vladimir Eidelman, Proceedings of the 2nd Workshop on
New Frontiers in Summarization, 2019. The dataset card in the publishers'
Hugging Face repository declares it under the
[CC0 1.0 Universal Public Domain Dedication](https://creativecommons.org/publicdomain/zero/1.0/legalcode).

The bill texts are works of the United States Congress, published by the United
States Government Publishing Office through govinfo. The reference summaries were
written by Legislative Analysts of the Congressional Research Service, a
department of the Library of Congress, and are published on Congress.gov. The
govinfo policies page asks that credit be given to the agency that prepared the
material:

```
In those instances in which permission to reprint material from Government
publications is granted, customary credit should be given to the Government
department or agency which prepared the material.
```

BillSum carries no canary string.
