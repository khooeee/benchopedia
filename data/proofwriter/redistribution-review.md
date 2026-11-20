# ProofWriter redistribution review

## Scope

The snapshot contains the complete open-world depth-5 test set: all 948
theories and 20,030 questions in `OWA/depth-5/meta-test.jsonl` from version
V2020.12.3 of the ProofWriter datasets, the archive
`proofwriter-dataset-V2020.12.3.zip` with SHA-256 digest
`bbc5694901e8306d0bd659aa1ad53ccfd02c201864f4b320ffa3777827d1fc26`. For each
question it includes the theory's text, the statement, the answer, the
published proofs of true and false answers, and the text of each fact and rule
those proofs cite. The formal representations, the proofs with intermediate
conclusions, the lists of every provable implication, the failed searches
given for unknown answers, and the archive's other files are not copied. Both
the public repository and the website publish this content. It is text only,
with no code or images.
[Archive](https://aristo-data-public.s3.amazonaws.com/proofwriter/proofwriter-dataset-V2020.12.3.zip)

## Terms

AI2's ProofWriter dataset page lists the dataset's license as "CC BY" and
links it to the Creative Commons Attribution 4.0 International license. The
three archived copies checked, from 2020-12-25, 2021-10-06, and 2024-02-27,
all show that license, and the last links the V2020.12.3 archive and its
README for download.
The page's address now redirects to the archive itself. The license permits
copying, redistribution, public display, and adaptation when the work is
credited, a link to the license is given, and changes are indicated. It adds
no non-commercial or share-alike condition. The paper points readers to the
same page for the datasets. Neither the archive, which has no license file,
nor its README states other terms, and the archive is downloaded directly
with no form, account, or click-through terms.
[Dataset page, archived 2020-12-25](https://web.archive.org/web/20201225020047/https://allenai.org/data/proofwriter),
[dataset page, archived 2024-02-27](https://web.archive.org/web/20240227065042/https://allenai.org/data/proofwriter),
[archive README](https://aristo-data-public.s3.amazonaws.com/proofwriter/proofwriter-dataset-V2020.12.3-README.md),
and [paper](https://arxiv.org/abs/2012.13048)

According to the README, the archive updates AI2's earlier RuleTaker
datasets, and theories without negation are the original RuleTaker theories.
AI2's RuleTaker page lists those datasets under the Apache License 2.0, which
also permits redistribution. AI2 publishes both, and it offers the ProofWriter
archive, including those theories, under CC BY 4.0, which this review applies.
[RuleTaker page, archived 2024-07-24](https://web.archive.org/web/20240724122349/https://allenai.org/data/ruletaker)

The text is generated from templates. The only names are eight first names
the templates use for people (Anne, Bob, Charlie, Dave, Erin, Fiona, Gary, and
Harry), and a scan of the imported text found no contact details or web
addresses.

## Changes

Benchopedia builds each task prompt from the theory's text, then the
statement after the label `Statement:`, then a question it adds that defines
true, false, and unknown under the open-world assumption. The theory and
statement are reproduced exactly as published.

The reference solution is the answer, written `True`, `False`, or `Unknown`,
followed for true and false answers by the published `proofs` field and one
line for each fact and rule it cites, labelled with its identifier, such as
`triple9` or `rule3`, and giving its text from the theory. Keys join the
theory's ID and the question's name, and source links point at the archive.

## Notices

ProofWriter is from "ProofWriter: Generating Implications, Proofs, and
Abductive Statements over Natural Language" by Oyvind Tafjord, Bhavana Dalvi
Mishra, and Peter Clark, Findings of the Association for Computational
Linguistics: ACL-IJCNLP 2021, published by the Allen Institute for AI. Its
datasets update those of "Transformers as Soft Reasoners over Language" by
Peter Clark, Oyvind Tafjord, and Kyle Richardson, IJCAI 2020. ProofWriter is
used under the [Creative Commons Attribution 4.0 International
license](https://creativecommons.org/licenses/by/4.0/).

ProofWriter carries no canary string.
