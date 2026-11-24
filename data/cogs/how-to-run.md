The input is the sentence in the authors' corrected generalization split.
The target is its canonical logical form. The [original study](https://aclanthology.org/2020.emnlp-main.731.pdf)
describes the notation in Section 3 and Appendices C and H.

### 1. Load this sentence

The key `{{key}}` identifies the one-based line number in the pinned TSV.
The third column names the generalization case.

```python
from urllib.request import urlopen

key = "{{key}}"
revision = "165a7b669eade971fa47bf568a2e51925360fed8"
url = f"https://raw.githubusercontent.com/najoungkim/COGS/{revision}/data/gen.tsv"

with urlopen(url, timeout=60) as response:
    rows = [tuple(line.decode("utf-8").rstrip("\r\n").split("\t")) for line in response]

sentence, reference, case = rows[int(key.split("-")[-1]) - 1]
```

### 2. Generate a COGS logical form

Send the tokenized sentence with the notation instructions. The paper trained
semantic parsers on the COGS training set. This chat prompt uses an example
to show the output notation.

```python
def generate(prompt):
    raise NotImplementedError("Call your model and return its logical form as text.")

def prompt_for(sentence):
    return sentence + "\n\n" + (
        "Translate the sentence above into its COGS logical form. Index words from 0 "
        "and use x_<index> for noun and event heads. Use proper names directly as "
        "constants. Put starred definite noun predicates first, each followed by a "
        "semicolon. Join the other predicates with AND in head order. For roles "
        "of the same event, follow the word order of their arguments. Use COGS roles "
        "such as .agent, .theme, .recipient, .ccomp, .xcomp and .nmod.<preposition>.\n\n"
        "Example for \"A poet admired the fox .\"\n"
        "* fox ( x _ 4 ) ; poet ( x _ 1 ) AND admire . agent ( x _ 2 , x _ 1 ) "
        "AND admire . theme ( x _ 2 , x _ 4 )\n\n"
        "Return only the logical form."
    )

prediction = generate(prompt_for(sentence))
```

### 3. Score the reply

Compare the ordered logical-form tokens for exact equality. The adapter allows
formatting such as `x_1` in place of `x _ 1` and preserves the case and order
of all tokens.

```python
import re

token = re.compile(r"[A-Za-z][A-Za-z0-9]*|[0-9]+|[^\s]")

def correct(prediction, reference):
    return token.findall(prediction) == token.findall(reference)

print(case, int(correct(prediction, reference)))
```

### Score the full generalization split

Compute overall accuracy and accuracy for each of the 21 cases. The authors'
[case index](https://github.com/najoungkim/COGS/blob/165a7b669eade971fa47bf568a2e51925360fed8/data/gen_cases_to_paper_sections.json)
links each case to the paper. The `cp_recursion`, `pp_recursion`, and
`obj_pp_to_subj_pp` cases belong to the structural group. The remaining
cases belong to the lexical group.

```python
from collections import Counter

total, hits = Counter(), Counter()
for sentence, reference, case in rows:
    prediction = generate(prompt_for(sentence))
    total[case] += 1
    hits[case] += correct(prediction, reference)

assert len(total) == 21 and set(total.values()) == {1000}
print("Overall", sum(hits.values()) / sum(total.values()))
for case in sorted(total):
    print(case, hits[case] / total[case])
```
