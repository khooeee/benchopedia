miniF2F has no scoring harness: following the [paper](https://arxiv.org/abs/2109.00110), a statement counts as proved when Lean accepts a proof of it without `sorry`, using the [pinned toolchain and mathlib](https://github.com/facebookresearch/miniF2F/blob/e4f113090ad82d64f8ce064d2f55b613a9b6bded/leanpkg.toml). The check below implements that rule. Lean runs tactic code from the proof, so check untrusted proofs inside a sandbox such as a container or disposable virtual machine.

### 1. Install Lean 3 and the project

Install [elan](https://github.com/leanprover/elan), which fetches the Lean 3.42.1 toolchain named in `leanpkg.toml`, then follow the repository's README to fetch and build mathlib. Run everything below from the `miniF2F` directory.

```sh
git clone https://github.com/facebookresearch/miniF2F
cd miniF2F
git checkout e4f113090ad82d64f8ce064d2f55b613a9b6bded
pip install mathlibtools==1.3.2  # provides leanproject
leanpkg configure
leanproject get-mathlib-cache
leanproject build
```

### 2. Load this task

Benchopedia's key `{{key}}` is the split, `test` or `valid`, a hyphen, and the theorem name. Each split is one Lean file; the statement is the declaration up to `:=`, and the file's opening imports and `open_locale` lines are its context.

```python
import re
from pathlib import Path

DECLARATION = re.compile(r"(theorem|lemma) (\S+)")

def load(split, name):
    lines = Path(f"lean/src/{split}.lean").read_text(encoding="utf-8").split("\n")
    starts = [i for i, line in enumerate(lines) if DECLARATION.match(line)]
    start = next(i for i in starts if DECLARATION.match(lines[i])[2] == name)
    begin = next(i for i in range(start, len(lines)) if lines[i].rstrip() == "begin")
    return "\n".join(lines[:starts[0]]), "\n".join(lines[start:begin])

key = "{{key}}"
split, name = key.split("-", 1)
preamble, statement = load(split, name)
```

### 3. Generate a proof

The model receives the formal statement and returns a Lean 3 proof to follow `:=`, normally a tactic block from `begin` to `end`. The paper's GPT-f searched one tactic at a time with Lean checking each step; any method that ends in a complete proof can be scored the same way.

```python
def generate(statement: str) -> str:
    raise NotImplementedError("Call your model and return a Lean 3 proof, such as begin ... end.")

proof = generate(statement)
```

### 4. Score it

The check writes the statement and proof after the split's preamble into a new file in the project and compiles it. The proof counts only if Lean reports no errors and no use of `sorry`.

```python
import subprocess

def proved(preamble, statement, proof):
    Path("lean/src/attempt.lean").write_text(f"{preamble}\n{statement}\n{proof}\n", encoding="utf-8")
    run = subprocess.run(["lean", "lean/src/attempt.lean"], capture_output=True, text=True)
    output = run.stdout + run.stderr
    return run.returncode == 0 and "error" not in output and "sorry" not in output

print("proved" if proved(preamble, statement, proof) else "not proved")
```

### Score the full benchmark

Every `theorem` in a split file is a benchmark problem; `lemma` declarations are helpers. The score is Pass@N, the share of a split's 244 statements proved within N attempts each. Use `valid` for development and report on `test`, naming N and the commit.

```python
names = [DECLARATION.match(line)[2] for line in Path("lean/src/test.lean").read_text(encoding="utf-8").split("\n")
         if line.startswith("theorem ")]
solved = 0
for n in names:
    preamble, statement = load("test", n)
    solved += any(proved(preamble, statement, generate(statement)) for _ in range(8))
print("test Pass@8:", solved / len(names))
```

### Verify with the Benchopedia sweep

Build the local grader image with
`docker build -f data/minif2f/Dockerfile.eval -t benchopedia-minif2f:e4f1130 data/minif2f`
and run `python3 runner/sweep.py minif2f --verify-grader`. The grader uses the
pinned Lean 3 executable, mathlib revision, and split preambles. It runs each
proof in a new network-isolated container and checks for incomplete proofs.
The sweep checks one proof per task for pass@1.
