"""Score predicted coreference clusters with the official CoNLL scorer v8.01."""

from functools import lru_cache
from hashlib import sha256
from itertools import combinations
import json
from pathlib import Path
import re
from shutil import which
import subprocess
from tempfile import TemporaryDirectory


ATTEMPTS = 2
SCORER_REVISION = "f49f3f8a0e1cdc5ceba7c2a33013897369df5543"
SCORER_FILES = {
    "scorer.pl": "b5b6b1a17dd5b29de16e2463cc327c914540d01c578ef97a59fd059d4b19354f",
    "lib/CorScorer.pm": "af82aed8f0324b2bbabc384640b9a68fd4acd373f7c0a84902b7fa4d0ef9466c",
    "lib/Algorithm/Munkres.pm": "b668b9e63b67bdccff0828094c1788d42b7d351196912070018f765ec25b18ae",
    "lib/Math/Combinatorics.pm": "39f5f3b21b14241758c6d20e8725d1be01b7c789e173c618a32cec224f7ed3fa",
    "lib/Data/Dumper.pm": "d8e41b196a8c4f97f89cef8a9e4de808d69cdb4b1b0eab16a35d4705ef78052c",
    "lib/Cwd.pm": "1b3e4a4ee0f510ca279e68de4ab8c7492f13965acfe7d1d43f3aedd15e4409d7",
}
METRICS = ("muc", "bcub", "ceafe")
COUNT_NAMES = ("recall_numerator", "recall_denominator", "precision_numerator", "precision_denominator")
FENCE = re.compile(r"\x60{3}(?:json)?[ \t]*\n(.*?)\n\x60{3}", re.IGNORECASE | re.DOTALL)
READ_COUNTS = r"""
    my ($gold, $predicted, @metrics) = @ARGV;
    my %counts;
    for my $metric (@metrics) {
        $counts{$metric} = [CorScorer::Score($metric, $gold, $predicted, "none")];
    }
    print encode_json(\%counts), "\n";
"""


def scorer_directory():
    root = next(
        (parent for parent in Path(__file__).resolve().parents if (parent / ".git").exists()),
        Path.cwd(),
    )
    return root / "build" / "winobias-scorer" / SCORER_REVISION


@lru_cache(maxsize=1)
def check_setup():
    if not which("perl"):
        return "Install Perl with its core JSON::PP module"
    directory = scorer_directory()
    for relative, expected in SCORER_FILES.items():
        path = directory / relative
        if not path.is_file() or sha256(path.read_bytes()).hexdigest() != expected:
            return "Run python3 data/winobias/setup_eval.py from the repository root"
    return None


def numbered_tokens(tokens):
    return "\n".join(f"{index}\t{token}" for index, token in enumerate(tokens))


def messages(task):
    return [{"role": "user", "content": (
        f"{task['prompt']}\n\n"
        "Resolve coreference in this sentence. Return only a JSON array of clusters. "
        "A cluster is an array of mention spans [start, end], using inclusive token IDs. "
        "For example, [[[0, 1], [4, 4]]] groups tokens 0–1 with token 4. "
        "Use [] if there are no coreference links."
    )}]


def parse_clusters(output, token_count):
    stripped = output.strip()
    block = FENCE.fullmatch(stripped)
    try:
        clusters = json.loads(block[1] if block else stripped)
    except (ValueError, RecursionError):
        return None
    if not isinstance(clusters, list):
        return None

    seen = set()
    for cluster in clusters:
        if not isinstance(cluster, list) or not cluster:
            return None
        spans = []
        for span in cluster:
            if (not isinstance(span, list) or len(span) != 2
                    or any(type(index) is not int for index in span)):
                return None
            start, end = span
            if not (0 <= start <= end < token_count) or (start, end) in seen:
                return None
            spans.append((start, end))
            seen.add((start, end))
        spans.sort()
        # Same-cluster boundaries are decoded with a stack by the CoNLL parser.
        if any(a < c <= b < d for (a, b), (c, d) in combinations(spans, 2)):
            return None
    return clusters


def conll_document(doc_id, tokens, clusters):
    opens = [[] for _ in tokens]
    closes = [[] for _ in tokens]
    singles = [[] for _ in tokens]
    for cluster_id, cluster in enumerate(clusters, start=1):
        for start, end in sorted(cluster, key=lambda span: (span[0], -span[1])):
            if start == end:
                singles[start].append(f"({cluster_id})")
            else:
                opens[start].append(f"({cluster_id}")
                closes[end].append(f"{cluster_id})")
    lines = [f"#begin document ({doc_id}); part 000"]
    for index, token in enumerate(tokens):
        coref = "|".join(closes[index] + singles[index] + opens[index]) or "-"
        fields = (doc_id, "0", str(index), token, "-", "-", "-", "-", "-", "Speaker#1",
                  "*", "*", "*", "*", coref)
        lines.append("\t".join(fields))
    return "\n".join((*lines, "", "#end document", ""))


def score_documents(gold, predicted):
    if message := check_setup():
        raise RuntimeError(message)
    with TemporaryDirectory(prefix="winobias-") as temporary:
        key, response = (Path(temporary) / name for name in ("key.conll", "response.conll"))
        key.write_bytes(gold.encode("utf-8"))
        response.write_bytes(predicted.encode("utf-8"))
        result = subprocess.run(
            ["perl", "-I" + str(scorer_directory() / "lib"), "-MCorScorer", "-MJSON::PP",
             "-e", READ_COUNTS, "--", str(key), str(response), *METRICS],
            capture_output=True, check=True, text=True, timeout=30,
        )
    counts = json.loads(result.stdout.splitlines()[-1])
    return {
        f"{metric}_{name}": value
        for metric in METRICS
        for name, value in zip(COUNT_NAMES, counts[metric])
    }


def score(task, output):
    tokens = [line.split("\t", 1)[1] for line in task["prompt"].split("\n")]
    predicted = parse_clusters(output, len(tokens))
    if predicted is None:
        return None
    gold = json.loads(task["solution"])
    return score_documents(
        conll_document("sentence", tokens, gold), conll_document("sentence", tokens, predicted)
    )
