"""Check complete Lean 3 proofs against the pinned miniF2F toolchain."""

from functools import lru_cache
import re
import subprocess
from uuid import uuid4


ATTEMPTS = 1
IMAGE = "benchopedia-minif2f:e4f1130"
REVISION = "e4f113090ad82d64f8ce064d2f55b613a9b6bded"
FENCE = re.compile(r"```(?:lean|lean3)?[ \t]*\n(.*?)\n```", re.DOTALL | re.IGNORECASE)
NO_PROOF = re.compile(r"\b(?:sorry|sorryAx|admit)\b", re.IGNORECASE)
PREAMBLES = {
    "test": "import minif2f_import\nopen_locale big_operators\nopen_locale nat\nopen_locale real\nopen_locale rat",
    "valid": "import minif2f_import\nopen_locale big_operators\nopen_locale real\nopen_locale nat\nopen_locale topological_space",
}

# The pinned test file defines this helper separately from the benchmark theorems.
# It is Apache 2.0 licensed. See the benchmark's LICENSE.
# https://github.com/facebookresearch/miniF2F/blob/e4f113090ad82d64f8ce064d2f55b613a9b6bded/lean/src/test.lean#L1613
TEST_HELPER = """lemma sum_pairs (n : ℕ) (f : ℕ → ℚ) :
  ∑ k in (finset.range (2 * n)), f k = ∑ k in (finset.range n), (f (2 * k) + f (2 * k + 1)) :=
begin
  induction n with pn hpn,
  { simp only [finset.sum_empty, finset.range_zero, mul_zero] },
  { have hs: (2 * pn.succ) = (2 * pn).succ.succ := rfl,
    rw [finset.sum_range_succ, ←hpn, hs, finset.sum_range_succ, finset.sum_range_succ],
    ring },
end"""


@lru_cache(maxsize=1)
def check_setup():
    try:
        inspect = subprocess.run(
            ["docker", "image", "inspect", "--format", '{{index .Config.Labels "org.benchopedia.minif2f"}}', IMAGE],
            capture_output=True, text=True, timeout=10,
        )
        if inspect.returncode == 0 and inspect.stdout.strip() == REVISION:
            return None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return ("Start Docker and run docker build -f data/minif2f/Dockerfile.eval "
            f"-t {IMAGE} data/minif2f")


def statement(task):
    _, marker, text = task["prompt"].partition("\n\n~~~lean\n")
    if not marker or not text.endswith("\n~~~"):
        raise ValueError(f"{task['key']}: missing Lean declaration")
    return text.removesuffix("\n~~~")


def messages(task):
    split = task["key"].split("-", 1)[0]
    return [{"role": "user", "content": (
        "Complete this Lean 3 theorem with a proof to follow :=. "
        "Return only the proof, without sorry.\n\n"
        f"{PREAMBLES[split]}\n\n{statement(task)}"
    )}]


def reference_output(task):
    return task["solution"].removeprefix(statement(task)).strip()


def grade(task, output):
    reply = output.strip()
    block = FENCE.fullmatch(reply)
    proof = block[1].strip() if block else reply
    if not proof:
        return "unparseable", None
    if NO_PROOF.search(proof):
        return "fail", "incomplete proof"
    split, theorem = task["key"].split("-", 1)
    helper = TEST_HELPER if split == "test" else ""
    program = f"{PREAMBLES[split]}\n{helper}\n\n{statement(task)}\n{proof}\n#print axioms {theorem}\n"
    container = f"benchopedia-lean-{uuid4().hex}"
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--init", "--name", container, "--pull=never",
             "--log-driver", "none", "--network", "none", "--read-only", "--cap-drop", "ALL",
             "--security-opt", "no-new-privileges", "--user", "65534:65534",
             "--memory", "2g", "--memory-swap", "2g", "--cpus", "4", "--pids-limit", "32",
             "--tmpfs", "/tmp:size=8m,mode=1777,noexec,nosuid", "-i", IMAGE],
            input=program, capture_output=True, text=True, timeout=120,
        )
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", container], capture_output=True, timeout=10)
        return "fail", "proof timed out"
    if result.returncode in (125, 126, 127):
        raise RuntimeError(f"Lean sandbox could not start: {result.stderr.strip()}")
    diagnostics = result.stdout + result.stderr
    if result.returncode or NO_PROOF.search(diagnostics) or not diagnostics.strip():
        return "fail", "Lean rejected the proof"
    return "pass", "Lean accepted the proof"
