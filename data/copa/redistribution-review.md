# COPA redistribution review

## Scope

The snapshot contains the complete COPA test set: the 500 questions of
`COPA-resources/datasets/copa-test.xml`, numbered 501 to 1000, and their answers
from `COPA-resources/results/gold.test`. Both files are inside the published
package `COPA-resources.tgz` ("Version 1. March 2011"), which is pinned by its
SHA-256 digest
`5145348834d2081ad90da0397d1db3d70fa044e506bd8ce224194d24b04cdbbe`. The
development set, the baseline answer files, and the significance-test program in
the same package are not imported. Both the public repository and the website
publish this content. It is text only: each question is three short English
sentences and a direction, with no images or code.

The publisher's addresses for the project page and the package no longer answer.
The snapshot is read from the Internet Archive's unmodified capture of the
package, taken on 2023-01-17. An earlier capture from 2022-08-04 has the same
content digest. The page offered the package as a plain download with no form,
account, or click-through terms.
[Project page, archived 2024-04-02](https://web.archive.org/web/20240402061922/https://people.ict.usc.edu/~gordon/copa.html)
and [package, archived 2023-01-17](https://web.archive.org/web/20230117124437/https://people.ict.usc.edu/~gordon/downloads/COPA-resources.tgz)

## Terms

The COPA project page publishes the BSD 2-Clause License for the evaluation,
under the heading "9. License (BSD 2-Clause License)", with the notice
"Copyright (c) 2010, University of Southern California". The statement first
appears in the Internet Archive's capture of 2020-06-25. The capture of
2020-05-13, and the earlier captures checked back to 2012, carry no license
statement. Every later capture checked carries it, through the capture of
2024-04-02, the last before the page stopped being served. The package itself contains no license file, so this
review relies on the page's statement, which the rights holder published for the
materials it distributes on that page. The license permits redistribution with or
without modification, provided that the copyright notice, the two conditions, and
the disclaimer are retained in source form and reproduced in the documentation
that accompanies other forms. Its wording is written for software. Benchopedia
treats both `tasks.jsonl` and the website as redistribution and reproduces the
notice, conditions, and disclaimer in full below, which meets both clauses.
[Project page, archived 2024-04-02](https://web.archive.org/web/20240402061922/https://people.ict.usc.edu/~gordon/copa.html)
and [project page, archived 2020-06-25](https://web.archive.org/web/20200625185937/https://people.ict.usc.edu/~gordon/copa.html)

The questions are the authors' own writing. The paper says the authors took
topics from weblog stories and from the Library of Congress Thesaurus for Graphic
Materials and then "elaborate[d] these topics into premises and alternatives
through our own creativity". No text from those topic sources is part of the
questions.
[Paper](https://web.archive.org/web/20210513111412/http://people.ict.usc.edu/~gordon/publications/AAAI-SPRING11A.PDF)

The project page also asks researchers not to study the 500 test questions and
to evaluate on them only once: "In providing both the development and test sets,
we are relying on competitors to exercise ethical research practices.
Researchers should not study the 500 questions in the COPA test set, and avoid
any temptation to alter their systems toward the content of this particular set
of questions." This is a request about research practice, not a condition on
redistribution. The publisher distributes the test questions and answers openly
in the same package. The benchmark page repeats the request in its limitations.

A scan of the imported text found no contact details, addresses, or other
personal data. By design the questions use no names of people or places.

## Changes

Benchopedia builds each task prompt from the premise, the question for its
direction, and the two alternatives. The question wording, "What was the CAUSE
of this?" or "What happened as a RESULT?", is taken from the readable question
file the publisher offers for the development set, where those are the only two
questions asked. The `Premise:`, `Alternative 1:`,
and `Alternative 2:` labels follow the examples on the project page. The
sentences are reproduced exactly as published. Alternative 2 of questions 691
and 705 begins with a space upstream, and the space is kept.

The reference solution is the correct alternative with its number, as recorded
in the question file's `most-plausible-alternative` attribute and in the
separate answer file, which agree for every question. Keys are the upstream
question numbers. The package records no per-question address, so the prompt
and solution links of every task point at the archived package the text came
from.

## Notices

COPA is from "Choice of Plausible Alternatives: An Evaluation of Commonsense
Causal Reasoning" by Melissa Roemmele, Cosmin Adrian Bejan, and Andrew S.
Gordon, AAAI Spring Symposium on Logical Formalizations of Commonsense
Reasoning, Stanford University, March 21–23, 2011. The license, as published on
the project page:

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

COPA carries no canary string.
