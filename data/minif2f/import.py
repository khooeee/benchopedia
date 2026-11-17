"""Import all 488 miniF2F Lean statements from a pinned commit of the task repository.

Run from the repository root: python3 data/minif2f/import.py
Only Python's standard library is required. Imported code is never executed.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

BENCHMARK_DIR = Path(__file__).resolve().parent
REPOSITORY = "facebookresearch/miniF2F"
# Upstream split name and its documented problem count.
SPLITS = {"valid": 244, "test": 244}
EXPECTED_COUNT = sum(SPLITS.values())
DECLARATION = re.compile(r"(theorem|lemma) (\S+)")


def fetch_lines(revision, split):
    url = f"https://raw.githubusercontent.com/{REPOSITORY}/{revision}/lean/src/{split}.lean"
    with urllib.request.urlopen(url, timeout=60) as response:
        return response.read().decode("utf-8").split("\n")


def declarations(lines):
    """Yield each Lean declaration as its kind, name, lines, and first line number."""
    starts = [number for number, line in enumerate(lines) if DECLARATION.match(line)]
    for position, start in enumerate(starts):
        stop = starts[position + 1] if position + 1 < len(starts) else len(lines)
        block = lines[start:stop]
        # A declaration ends at its own `end`; later blank or comment lines
        # introduce the next declaration.
        while block and (not block[-1].strip() or block[-1].lstrip().startswith("--")):
            block.pop()
        kind, name = DECLARATION.match(block[0]).groups()
        yield kind, name, block, start + 1


def to_task(split, name, block, first_line, revision):
    where = f"{split}/{name}"
    if block[-1].rstrip() != "end":
        raise ValueError(f"{where}: declaration does not end with end")
    proof_starts = [number for number, line in enumerate(block) if line.rstrip() == "begin"]
    if len(proof_starts) != 1:
        raise ValueError(f"{where}: expected one tactic proof block")
    statement = "\n".join(block[:proof_starts[0]])
    if not statement.rstrip().endswith(":="):
        raise ValueError(f"{where}: statement does not end with :=")
    if "~~~" in statement:
        raise ValueError(f"{where}: statement cannot be fenced intact")
    source = (f"https://github.com/{REPOSITORY}/blob/{revision}/lean/src/{split}.lean"
              f"#L{first_line}-L{first_line + len(block) - 1}")
    task = {
        "key": f"{split}-{name}",
        "prompt": f"{where}\n\n~~~lean\n{statement}\n~~~",
        # A proof containing sorry is unfinished, so it is not a reference solution.
        "solution": None if "sorry" in "\n".join(block) else "\n".join(block),
        "prompt_source_url": source,
        "solution_source_url": source,
        "environment_url": f"https://github.com/{REPOSITORY}/blob/{revision}/leanpkg.toml",
    }
    if task["solution"] is None:
        del task["solution"], task["solution_source_url"]
    return task


def main():
    benchmark = json.loads((BENCHMARK_DIR / "benchmark.json").read_text(encoding="utf-8"))
    revision = benchmark["dataset_revision"]
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        sys.exit("dataset_revision must be an immutable GitHub commit SHA.")
    if benchmark["task_count"] != EXPECTED_COUNT:
        sys.exit("The declared scope must be all 488 miniF2F Lean statements.")
    tasks = []
    for split, count in SPLITS.items():
        found = 0
        for kind, name, block, first_line in declarations(fetch_lines(revision, split)):
            # Helper lemmas support a neighbouring proof and are not benchmark problems.
            if kind == "lemma":
                continue
            tasks.append(to_task(split, name, block, first_line, revision))
            found += 1
        if found != count:
            sys.exit(f"{split}: expected {count} theorems, found {found}.")
    tasks.sort(key=lambda task: task["key"])
    if len({task["key"] for task in tasks}) != EXPECTED_COUNT:
        sys.exit("miniF2F problem names differ from the declared scope.")
    if not any("solution" in task for task in tasks):
        sys.exit("Expected the Lean files to supply reference proofs.")
    out = BENCHMARK_DIR / "tasks.jsonl"
    temporary = out.with_suffix(".jsonl.tmp")
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as stream:
            for task in tasks:
                stream.write(json.dumps(task, ensure_ascii=False) + "\n")
        temporary.replace(out)
    finally:
        temporary.unlink(missing_ok=True)
    proved = sum("solution" in task for task in tasks)
    print(f"Wrote {len(tasks):,} miniF2F statements ({proved} with proofs) to {out}")


if __name__ == "__main__":
    main()
