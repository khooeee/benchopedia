COPA is scored as accuracy: the fraction of questions on which a system picks the more plausible alternative. The authors' [evaluation package](https://web.archive.org/web/20230117124437/https://people.ict.usc.edu/~gordon/downloads/COPA-resources.tgz) holds the questions, the gold answers and `copa-eval.sh`, which reports two systems' accuracy and whether they differ significantly.

### 1. Download the package

The publisher's address no longer serves the package, so fetch the Internet Archive's unmodified copy and check it is the version this snapshot was imported from.

```sh
curl -LO "https://web.archive.org/web/20230117124437id_/https://people.ict.usc.edu/~gordon/downloads/COPA-resources.tgz"
echo "5145348834d2081ad90da0397d1db3d70fa044e506bd8ce224194d24b04cdbbe  COPA-resources.tgz" | shasum -a 256 -c
tar -xzf COPA-resources.tgz
```

### 2. Load this task

Benchopedia's key `{{key}}` is the upstream question number in `copa-test.xml`.

```python
import xml.etree.ElementTree as ElementTree

key = "{{key}}"
corpus = ElementTree.parse("COPA-resources/datasets/copa-test.xml").getroot()
item = next(item for item in corpus if item.get("id") == key)
premise, first, second = (child.text for child in item)
```

### 3. Generate an answer

The prompt follows the project page's examples: the premise, the question for the item's direction, then the two numbered alternatives.

```python
QUESTIONS = {"cause": "What was the CAUSE of this?", "effect": "What happened as a RESULT?"}

def generate(prompt: str) -> str:
    raise NotImplementedError("Call your model and return the number of the more plausible alternative, 1 or 2.")

prompt = (f"Premise: {premise} {QUESTIONS[item.get('asks-for')]}\n\n"
          f"Alternative 1: {first}\n\nAlternative 2: {second}")
prediction = generate(prompt).strip()
```

### 4. Score it

The question file records the gold answer as `most-plausible-alternative`, the same choice `results/gold.test` marks.

```python
print(prediction == item.get("most-plausible-alternative"))
```

### Score the full benchmark

Write `COPA-resources/answers.test` with one line per question, numbers 501 to 1000 in order, in the package's format: `501 1 0` when the model chose alternative 1 and `501 0 1` when it chose alternative 2. Then compare it with the best-performing baseline from the authors' paper. The script needs Java and prints `system_1 acc`, your accuracy over all 500 questions, then the baseline's accuracy and a p-value for the difference.

```sh
cd COPA-resources
./copa-eval.sh results/gold.test answers.test results/PMIgutenbergW5.test
```

lm-evaluation-harness's `copa` task scores SuperGLUE's validation questions, not this test set.
