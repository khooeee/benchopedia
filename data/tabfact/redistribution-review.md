# TabFact redistribution review

## Scope

The snapshot contains TabFact's complete test split: the 12,779 statements and
labels in `tokenized_data/test_examples.json` at commit
`2ab782ba42b5808076ac91fec846473aa5315a79` of wenhuchen/Table-Fact-Checking,
with each table's caption, and the 1,695 tables they refer to, copied from
`data/all_csv` at the same commit. The Wikipedia page recorded for each table in
`data/table_to_page.json` is listed in the accompanying `ATTRIBUTION.md`. The
training and validation splits, the raw crowdsourced files, the challenge's
blind test, the preprocessed data, and the repository's code and images are
not copied. Both the public repository and the website publish this content.
It is text only, with no code or images.
[Repository at the pinned commit](https://github.com/wenhuchen/Table-Fact-Checking/tree/2ab782ba42b5808076ac91fec846473aa5315a79)

## Terms

The project website says: "The dataset is under a Creative Commons
Attribution 4.0 International License," linking that license. The
repository's `LICENSE` at the pinned commit is the MIT License, with the notice
"Copyright (c) 2019 wenhu chen", and GitHub identifies the repository's license
as MIT; it was added on 2019-09-04, before the test statements file. Both
licenses permit copying, redistribution, public display, and adaptation. CC BY
4.0 requires that the work be credited, a link to the license be given, and
changes be indicated; the MIT License requires that its copyright and
permission notices be included with copies. Neither adds a non-commercial,
share-alike, or research-only condition, and this snapshot meets both. The
README states no other terms and asks users to cite the paper, which is
credited below. The files are downloaded directly from GitHub with no form,
account, or click-through terms, and the paper says the authors released all
the data and code.
[Project website source](https://github.com/tabfact/tabfact.github.io/blob/3bc35764546d8ff5a4e31f82dcc827dd7538d2bc/index.html),
[license at the pinned commit](https://github.com/wenhuchen/Table-Fact-Checking/blob/2ab782ba42b5808076ac91fec846473aa5315a79/LICENSE),
[README](https://github.com/wenhuchen/Table-Fact-Checking/blob/2ab782ba42b5808076ac91fec846473aa5315a79/README.md),
and [paper](https://arxiv.org/abs/1909.02164)

The statements were written by Amazon Mechanical Turk workers the authors
hired. The tables were taken from English Wikipedia pages for the WikiTables
collection, so they carry Wikipedia's own terms as well. Wikipedia text is
shared under CC BY-SA, and Wikipedia's reuse guidance accepts a link to the
article as credit to its contributors; earlier CC BY-SA versions allow
adaptations under version 4.0, so publishing these tables under CC BY-SA 4.0
is consistent with Wikipedia's terms. The dataset records the source page of
1,608 of the 1,695 test tables, by title and link, and each of those tables'
captions is its page title, which every task prompt for the table shows.
`ATTRIBUTION.md` links all 1,608 pages. For the other 87 tables the dataset
records no page and the caption "none"; they are credited to English Wikipedia
contributors and listed in `ATTRIBUTION.md` without a page. The dataset does
not record which revision of each page the tables came from, so the links
point at the current pages.
[Wikipedia's reuse terms](https://en.wikipedia.org/wiki/Wikipedia:Reusing_Wikipedia_content)
and [table-to-page mapping](https://github.com/wenhuchen/Table-Fact-Checking/blob/2ab782ba42b5808076ac91fec846473aa5315a79/data/table_to_page.json)

A scan of the imported text found no contact details or web addresses. The
tables record what Wikipedia records about public figures, such as athletes'
results, politicians' elections, and performers' credits. The project website
gives the first author's email address; it is not reproduced here.

## Changes

Benchopedia assembles each task prompt from the table's caption, unless the
caption is "none", the table file inside a fenced block, the statement, and a
question that notes the `#` cell separator and asks whether the statement is
entailed or refuted. The table files' Windows line breaks become plain line
breaks; the caption, table, and statement text is otherwise unchanged. The
reference solution writes the label 1 as `Entailed` and 0 as `Refuted`. Keys
join the table's file name and the statement's position in its list, and
source links point at the statements file and table file at the pinned commit.

## Notices

TabFact is from "TabFact: A Large-scale Dataset for Table-based Fact
Verification" by Wenhu Chen, Hongmin Wang, Jianshu Chen, Yunkai Zhang, Hong
Wang, Shiyang Li, Xiyou Zhou, and William Yang Wang, ICLR 2020, published in
the wenhuchen/Table-Fact-Checking repository. The statements were written by
crowdworkers.

The 1,695 tables were extracted from English Wikipedia pages by Wikipedia
contributors. The pages the dataset records are credited by title and link in
the `ATTRIBUTION.md` that accompanies this snapshot, and each task prompt for
those tables names its page in the caption.

The dataset is used under the [Creative Commons Attribution 4.0 International
license](https://creativecommons.org/licenses/by/4.0/), and the tables are
shared under the [Creative Commons Attribution-ShareAlike 4.0 International
license](https://creativecommons.org/licenses/by-sa/4.0/legalcode). Adaptations
of these tables must remain under those terms. Benchopedia's MIT license does
not replace them.

The repository's license, which accompanies this snapshot as `LICENSE`:

```
MIT License

Copyright (c) 2019 wenhu chen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

TabFact carries no canary string.
