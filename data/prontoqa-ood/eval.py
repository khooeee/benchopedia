"""Run the authors' atomic proof checker on a chat response."""

from hashlib import sha256
from importlib import import_module
from importlib.machinery import ModuleSpec
from importlib.util import module_from_spec
from pathlib import Path
import sys


ATTEMPTS = 2
CAPTURE_FILES = (
    "data/prontoqa-ood/upstream/bad_patterns.txt",
    "data/prontoqa-ood/upstream/checker.py",
    "data/prontoqa-ood/upstream/fol.py",
    "data/prontoqa-ood/upstream/syntax.py",
)
INSTRUCTION = "Write just the proof, with each step as a complete sentence like the examples."


def load_checker():
    # Separate module namespaces keep captured graders independent during replay.
    path = Path(__file__).resolve().with_name("upstream")
    namespace = "_benchopedia_prontoqa_" + sha256(str(path).encode()).hexdigest()
    if namespace not in sys.modules:
        spec = ModuleSpec(namespace, loader=None, is_package=True)
        spec.submodule_search_locations = [str(path)]
        sys.modules[namespace] = module_from_spec(spec)
    return import_module(f"{namespace}.checker")


def messages(task):
    return [{"role": "user", "content": f"{task['prompt']}\n\n{INSTRUCTION}"}]


def grade(task, output):
    checker = load_checker()
    answer = output.strip()
    proof, label, errors = checker.parse_response(answer)
    if not any(step is not None for step in proof):
        return "unparseable", None

    test = task["prompt"].rsplit("\n\nQ: ", 1)[-1]
    premises = test.split(" Prove: ", 1)[0]
    axioms = checker.parse_reasoning(premises, errors)
    result = checker.evaluate_response(proof, label, task["solution"], axioms, True, errors)
    # The authors report found_conclusion as strict proof accuracy.
    return ("pass" if result[13] else "fail"), answer
