The [original ListOps paper](https://aclanthology.org/N18-4013/) measures
ten-way classification accuracy. The authors' [loader](https://github.com/NYU-MLL/spinn/blob/1e2805c7b0b327db5d9d78e9b7792ad31678edfa/python/spinn/data/listops/load_listops_data.py)
separates the token sequence from the reference binary parse. Their
[label generator](https://github.com/NYU-MLL/spinn/blob/1e2805c7b0b327db5d9d78e9b7792ad31678edfa/python/spinn/data/listops/make_data.py)
defines the arithmetic and the digit labels.

### 1. Load this task

The key `{{key}}` contains the one-based line number in the pinned original
test file. The steps use Python 3.9 or later.

```python
from urllib.request import urlopen

key = "{{key}}"
revision = "1e2805c7b0b327db5d9d78e9b7792ad31678edfa"
url = (f"https://raw.githubusercontent.com/NYU-MLL/spinn/{revision}/"
       "python/spinn/data/listops/test_d20s.tsv")
with urlopen(url, timeout=60) as response:
    lines = response.read().decode("utf-8").splitlines()

def read_example(line):
    answer, binary_tree = line.split("\t")
    tokens = [token for token in binary_tree.split(" ") if token not in {"(", ")"}]
    return " ".join(tokens), answer

expression, reference = read_example(lines[int(key.removeprefix("listops-")) - 1])
```

### 2. Generate the digit

Keep the square brackets and operator tokens. Each closing square bracket
ends the list that begins at its matching operator. For even-length lists,
the median is the mean of the two middle numbers, rounded down.

```python
def generate(prompt):
    raise NotImplementedError("Call your model and return a single digit.")

intro = (
    "Evaluate this ListOps expression. MIN and MAX take the smallest or largest value. "
    "MED takes the median and rounds down. SM sums the values modulo 10. "
    "Evaluate the inner lists before using their results in the enclosing lists."
)

def make_prompt(expression):
    return f"{intro}\n\n{expression}\n\nReply with one digit."

prediction = generate(make_prompt(expression))
```

### 3. Score it

The reference label is a digit from 0 to 9. Compare the model's one-digit
response with that label.

```python
def correct(prediction, reference):
    return prediction.strip() == reference

print(correct(prediction, reference))
```

### Score the full benchmark

The original loader skips sequences of length one. Run the 9,999 nested
expressions in the 10,000-row test file and report accuracy over those
expressions. The catalog also includes the bare digit on line 4,259.

```python
assert len(lines) == 10_000
hits = total = 0
for line in lines:
    expression, reference = read_example(line)
    if len(expression) > 1:
        hits += correct(generate(make_prompt(expression)), reference)
        total += 1
assert total == 9_999
print(hits / total)
```
