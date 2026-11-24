# GraphQA Basic Zero-Shot redistribution review

## Scope

Benchopedia publishes the graph descriptions, questions, and reference
answers from the seven basic `zero_shot_test` configurations at revision
`ca8b67f4961e4110c949e81d20b829b6af59cad1`. The 3,500 records use integer
node IDs and synthetic Erdős–Rényi graphs in the adjacency encoding.
[Pinned GraphQA release](https://huggingface.co/datasets/baharef/GraphQA/tree/ca8b67f4961e4110c949e81d20b829b6af59cad1) ·
[Original study, Appendix A.2](https://openreview.net/pdf?id=IuXR1CCrSi)

## Terms

The lead author's pinned dataset card declares Creative Commons
Attribution 4.0 International for the dataset. The selected files are
public and available without authentication or approval. The license
permits public sharing and adaptation with credit, a license link, and
an indication of changes.
[Pinned dataset card](https://huggingface.co/datasets/baharef/GraphQA/blob/ca8b67f4961e4110c949e81d20b829b6af59cad1/README.md) ·
[CC BY 4.0 license text](https://creativecommons.org/licenses/by/4.0/legalcode.en)

## Changes

The importer converts the JSON records to JSONL and adds stable keys
and pinned source links. It preserves the published question and answer
strings, including their whitespace. The chat evaluator adds answer-format
instructions and normalizes reply punctuation, letter case, and node order
for scoring.

## Notices

GraphQA by Bahare Fatemi, Jonathan Halcrow, and Bryan Perozzi, released
under Creative Commons Attribution 4.0 International.
[Original study](https://openreview.net/forum?id=IuXR1CCrSi) ·
[Original data](https://huggingface.co/datasets/baharef/GraphQA/tree/ca8b67f4961e4110c949e81d20b829b6af59cad1) ·
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
