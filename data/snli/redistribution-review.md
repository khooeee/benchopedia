# SNLI redistribution review

## Scope

The snapshot contains the complete official test split of SNLI 1.0: the 10,000
sentence pairs of `snli_1.0/snli_1.0_test.jsonl` inside the published archive
`snli_1.0.zip`, pinned by its SHA-256 digest
`afb3d70a5af5d8de0d9d81e2637e0fb8c22d1235c2749d83125ca43dab0dbd3e`, with the
gold label and the individual annotator judgements of each pair. The training
and development splits, the parse trees the records carry beside each sentence,
and the separately published hard subset are not imported. Both the public
repository and the website publish this content. It is text only: no images,
code, or photographs are copied, and the archive contains none. The copy read is
the one the project page names, "SNLI is archived at the NYU Faculty Digital
Archive", reached without an account or a request form; the Stanford download has
been unreachable throughout this review.
[Dataset record](https://archive.nyu.edu/handle/2451/41728) and
[project page, archived 2026-10-07](https://web.archive.org/web/20261007202555/https://nlp.stanford.edu/projects/snli/)

## Terms

SNLI is published under a Creative Commons Attribution-ShareAlike 4.0
International license. The project page states: "The Stanford Natural Language
Inference Corpus by The Stanford NLP Group is licensed under a Creative Commons
Attribution-ShareAlike 4.0 International License. Based on a work at
http://shannon.cs.illinois.edu/DenotationGraph/." The NYU Faculty Digital
Archive record for the corpus repeats it in its rights field: "Dataset licensed
as CC-BY-SA 4.0. Paper licensed as CC-BY-NC-SA 3.0". Only the dataset is
imported. That license permits reproduction and distribution in any medium when
the work is credited, the license is named, and adaptations are shared under the
same or a compatible license, so this snapshot carries the notices below.
[Project page, archived 2026-10-07](https://web.archive.org/web/20261007202555/https://nlp.stanford.edu/projects/snli/),
[dataset record](https://archive.nyu.edu/handle/2451/41728), and
[legal code](https://creativecommons.org/licenses/by-sa/4.0/legalcode)

The premises come from a second corpus, and the publishers state its terms. The
distribution's readme says of the premise sentences: "Except where otherwise
marked, they are drawn from the Flickr30k corpus and are licenced as
CreativeCommons Attribution-ShareAlike", citing Young, Lai, Hodosh, and
Hockenmaier 2014; the project page repeats that Flickr30k was "also released
under an Attribution-ShareAlike licence". The exception the readme marks is the
pilot material taken from VisualGenome, whose pair and caption identifiers begin
`vg_`; the readme places it in the training set, and the importer confirms that
no record of this split carries such an identifier, so none of it is imported.

One point is recorded rather than resolved. The Flickr30k authors' own page
publishes no license text for their captions: it offers the corpus through a
request form and restricts the photographs, saying "Use of the images must abide
by the Flickr Terms of Use. We do not own the copyright of the images. They are
solely provided at the link below for researchers and educators who wish to use
the dataset for non-commercial research and/or educational purposes." That
restriction is written about the images. This snapshot contains no images and no
image addresses: the premises are the crowd-written caption sentences, which the
SNLI publishers state are Attribution-ShareAlike material and which they
redistribute themselves without a gate under the license above.
[Flickr30k and Denotation Graph page](http://shannon.cs.illinois.edu/DenotationGraph/)

A scan of the imported text found no contact details, addresses, or other
personal data, and no URLs. The sentences describe people in photographs in
general terms and name no one; the photographs themselves are not part of the
corpus.

## Changes

Benchopedia assembles each task prompt from the premise, the hypothesis, and the
question the annotators were answering. Both sentences are reproduced exactly as
published, each introduced by a `Premise:` or `Hypothesis:` label. The upstream
caption and pair identifiers are kept out of the prompt, because the readme warns
that they "contain information that can be useful in making classification
decisions and should not be included in model input".

The reference solution is the gold label as published, followed by a line listing
the annotator judgements in the upstream order. For the 176 pairs whose gold
label upstream records as `-`, meaning no label won a majority, the solution
writes `- (no majority label)` so the marker is readable; nothing else is added
or removed. Keys are the upstream pair identifiers, which contain a `#`. The
upstream file records no per-pair address, so the prompt and solution links of
every task point at the published archive the text came from.

## Notices

SNLI is from "A large annotated corpus for learning natural language inference"
by Samuel R. Bowman, Gabor Angeli, Christopher Potts, and Christopher D.
Manning, Proceedings of the 2015 Conference on Empirical Methods in Natural
Language Processing. The corpus notice, from the project page, is reproduced as
published:

```
The Stanford Natural Language Inference Corpus by The Stanford NLP Group is
licensed under a Creative Commons Attribution-ShareAlike 4.0 International
License. Based on a work at http://shannon.cs.illinois.edu/DenotationGraph/.
```

The premise sentences are from the Flickr30k corpus of Peter Young, Alice Lai,
Micah Hodosh, and Julia Hockenmaier, "From image descriptions to visual
denotations: new similarity metrics for semantic inference over event
descriptions", Transactions of the Association for Computational Linguistics 2:
67–78, 2014, which the distribution's readme records as Creative Commons
Attribution-ShareAlike material. The hypotheses were written by crowdworkers
hired by the SNLI authors.

Both grants are share-alike: an adaptation of this material must stay under the
[Creative Commons Attribution-ShareAlike 4.0 International license](https://creativecommons.org/licenses/by-sa/4.0/legalcode)
or a compatible later version of those terms. Benchopedia's MIT license does not
replace them.

SNLI carries no canary string.
