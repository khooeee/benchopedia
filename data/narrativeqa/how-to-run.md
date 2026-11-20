The NarrativeQA authors publish no scorer. Their [paper](https://arxiv.org/abs/1712.07040v1) scores free-text answers with BLEU-1, BLEU-4, METEOR and ROUGE-L against both reference answers. It first lowercases the answer and references and drops the final full stop. This guide implements that rule with [NLTK](https://pypi.org/project/nltk/3.10.4/)'s BLEU and METEOR and a short ROUGE-L. Papers used various implementations, so results can differ slightly from theirs. In particular, NLTK's METEOR is the original 2007 metric, not the Meteor 1.3 the paper cites.

### 1. Install the metrics and fetch the data

```sh
pip install "nltk==3.10.4"
python -m nltk.downloader wordnet  # METEOR's synonym matching reads WordNet
for f in qaps.csv third_party/wikipedia/summaries.csv; do
  curl -LO "https://raw.githubusercontent.com/google-deepmind/narrativeqa/904246f6d1fe99a99a08a03501fe3e619af2cee5/$f"
done
```

### 2. Load this task

Upstream questions have no IDs. Benchopedia's key `{{key}}` is the story's `document_id`, a hyphen, and the question's position among that story's rows in `qaps.csv`, counting from 1.

```python
import csv

key = "{{key}}"
document, number = key.rsplit("-", 1)
with open("qaps.csv", newline="", encoding="utf-8") as f:
    row = [r for r in csv.DictReader(f) if r["document_id"] == document][int(number) - 1]
with open("summaries.csv", newline="", encoding="utf-8") as f:
    summary = next(r["summary"] for r in csv.DictReader(f) if r["document_id"] == document)
```

### 3. Generate an answer

In the summary setting, for which the questions were written, the model reads the Wikipedia plot summary and the question and writes a short free-text answer.

```python
def generate(question: str, summary: str) -> str:
    raise NotImplementedError("Call your model and return its answer.")

answer = generate(row["question"], summary.strip())
```

### 4. Score it

ROUGE-L here follows the coco-caption toolkit: it takes the best precision and recall of the longest common subsequence over the references and weights them with β = 1.2. BLEU and METEOR use both references.

```python
import re
from nltk.translate.bleu_score import sentence_bleu
from nltk.translate.meteor_score import meteor_score

def tokens(text):
    words = re.findall(r"\w+|[^\w\s]", text.lower())
    return words[:-1] if words[-1:] == ["."] else words

def lcs(a, b):
    row = [0] * (len(b) + 1)
    for x in a:
        previous, row = row, [0]
        for j, y in enumerate(b):
            row.append(previous[j] + 1 if x == y else max(previous[j + 1], row[j]))
    return row[-1]

def rouge_l(candidate, references, beta=1.2):
    common = [lcs(candidate, reference) for reference in references]
    p = max(c / len(candidate) for c in common) if candidate else 0.0
    r = max(c / len(reference) for c, reference in zip(common, references))
    return (1 + beta**2) * p * r / (r + beta**2 * p) if p and r else 0.0

candidate = tokens(answer)
references = [tokens(row["answer1"]), tokens(row["answer2"])]
bleu1, bleu4 = sentence_bleu(references, candidate, weights=[(1,), (0.25, 0.25, 0.25, 0.25)])
print({"bleu1": bleu1, "bleu4": bleu4, "meteor": meteor_score(references, candidate),
       "rouge_l": rouge_l(candidate, references)})  # each from 0 to 1
```

### Score the full benchmark

Run steps 2 to 4 for all 10,557 test questions. Average METEOR and ROUGE-L over the questions. Compute BLEU over the whole split, which avoids sentence-level BLEU-4 being zero for most short answers. Papers usually report each metric multiplied by 100.

```python
from nltk.translate.bleu_score import corpus_bleu

# all_references holds each question's two token lists; all_candidates holds the answers' tokens.
bleu1, bleu4 = corpus_bleu(all_references, all_candidates, weights=[(1,), (0.25, 0.25, 0.25, 0.25)])
```

### Verify with the Benchopedia sweep

The sweep uses the compiled [Meteor 1.3 release](https://www.cs.cmu.edu/~alavie/METEOR/index.html)
cited by the paper. Install Java, run `python3 data/narrativeqa/setup_eval.py`,
and run `python3 runner/sweep.py narrativeqa --verify-grader`. Each task record
contains METEOR 1.3, ROUGE-L, and sentence-level BLEU-1 and BLEU-4. For a complete
test split, compute the corpus BLEU described above from the saved raw answers
and both references.
