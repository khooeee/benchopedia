# XSTest redistribution review

## Scope

The snapshot contains all 450 prompts and their safe or unsafe labels in xstest_prompts.csv at commit `d7bb5bd738c1fcbc36edd83d5e7d1b71a3e2d84d` of paul-rottger/xstest. The model completions and automated evaluation labels in the repository are not included. Both the public repository and the website publish the prompts and labels. No code or images are copied. [Prompt file](https://github.com/paul-rottger/xstest/blob/d7bb5bd738c1fcbc36edd83d5e7d1b71a3e2d84d/xstest_prompts.csv)

## Terms

The README at the pinned commit states that XSTest prompts are subject to the Creative Commons Attribution 4.0 International license, and the repository contains that license's full legal text. The license permits copying, redistribution, public display, and adaptation when the work is credited, a link to the license is given, and changes are stated. It adds no non-commercial or share-alike condition. The README places the model completions under their model providers' terms; those completions are not imported. [README](https://github.com/paul-rottger/xstest/blob/d7bb5bd738c1fcbc36edd83d5e7d1b71a3e2d84d/readme.md) and [license text](https://github.com/paul-rottger/xstest/blob/d7bb5bd738c1fcbc36edd83d5e7d1b71a3e2d84d/LICENSE)

The paper states that the authors created the prompts for this test suite. The repository has no access gate or separate restriction on publishing the prompts. [Paper](https://aclanthology.org/2024.naacl-long.301/)

## Changes

Benchopedia converts each CSV row into a task record, builds IDs from the upstream ID and prompt type, stores the label as the reference answer, and adds source links. The focus word and note columns are left out. Prompt and label text is unchanged.

## Notices

XSTest is from "XSTest: A Test Suite for Identifying Exaggerated Safety Behaviours in Large Language Models" by Paul Röttger, Hannah Rose Kirk, Bertie Vidgen, Giuseppe Attanasio, Federico Bianchi, and Dirk Hovy, published at NAACL 2024 and in the paul-rottger/xstest repository. The prompts are used under the [Creative Commons Attribution 4.0 International license](https://creativecommons.org/licenses/by/4.0/). The full license text from the pinned commit accompanies this snapshot as LICENSE.
