# Declined benchmark candidates

These benchmarks were considered for import and not added because the
[required redistribution review](../adding-a-benchmark.md#required-redistribution-review)
could not clear their tasks for both the public repository and the website. No
task content was copied for them. Each entry names what is unclear and what
would allow the import to resume.

## DROP

Reviewed 2026-11-16 for the development set in the official
[`drop_dataset.zip`](https://ai2-public-datasets.s3.amazonaws.com/drop/drop_dataset.zip).

The passages are Wikipedia text. The paper says they were extracted from an
October 2018 Wikipedia dump and online Wikipedia, mostly NFL game summaries and
history articles. [Original paper](https://arxiv.org/abs/1903.00161)

The publishers' terms conflict. The Allen Institute's dataset page, as archived
on 2022-12-09, listed the license as
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0). That page now
redirects to an evaluation script with no license statement. The
[Hugging Face card at `95cda593fae71b60b5b19f82de3fcf3298c1239c`](https://huggingface.co/datasets/ucinlp/drop/blob/95cda593fae71b60b5b19f82de3fcf3298c1239c/README.md)
declares CC BY-SA 4.0 instead. Wikipedia text is shared under CC BY-SA, which
requires attribution to the source article and its authors. The card lists each
record's fields as a section ID, query ID, passage, question, and answers; none
names the source Wikipedia article, so Benchopedia cannot provide that
attribution.
[Archived dataset page](https://web.archive.org/web/20221209012021/https://allenai.org/data/drop)

Resume when the publisher states one set of terms for the passages and
questions, and the source Wikipedia article for each passage can be identified
for attribution.
