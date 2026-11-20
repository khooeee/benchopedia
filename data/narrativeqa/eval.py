"""Score NarrativeQA summary answers with both human references.

The metric definitions follow section 4 of the paper:
https://arxiv.org/abs/1712.07040v1
METEOR runs the authors' cited 1.3 release from Carnegie Mellon.
"""

from collections import Counter
from functools import lru_cache
from pathlib import Path
from queue import Empty, Queue
import atexit
import hashlib
import math
import re
import shutil
import subprocess
from threading import Lock, Thread


ATTEMPTS = 1
METEOR_FILES = {
    "meteor-1.3.jar": "8b90784d4ca14272b2d89365458fcaf7fd17a2799dbcfc2349dacc38e5efcf2d",
    "data/paraphrase-en.gz": "c147ac7d2c91f2fbb3ad31e4b352235061eb83145e0434daf217ee9ca5975f48",
}
METEOR_LOCK = Lock()
TOKENS = re.compile(r"\w+|[^\w\s]")


def metric_dir():
    root = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
    return root / "build" / "narrativeqa-meteor"


@lru_cache(maxsize=1)
def check_setup():
    if shutil.which("java") is None:
        return "Install a Java runtime for METEOR 1.3"
    for name, digest in METEOR_FILES.items():
        path = metric_dir() / name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            return "Run python3 data/narrativeqa/setup_eval.py to install the pinned METEOR files"
    return None


class Meteor:
    def __init__(self, path):
        self.process = subprocess.Popen(
            ["java", "-Xmx768m", "-jar", "meteor-1.3.jar", "-", "-", "-l", "en",
             "-t", "rank", "-mira", "-a", "data/paraphrase-en.gz"],
            cwd=path, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            text=True, encoding="utf-8",
        )
        self.replies = Queue()
        Thread(target=self.read_replies, daemon=True).start()
        atexit.register(self.close)

    def read_replies(self):
        for line in self.process.stdout:
            self.replies.put(line.strip())
        self.replies.put(None)

    def request(self, command):
        try:
            self.process.stdin.write(command + "\n")
            self.process.stdin.flush()
            response = self.replies.get(timeout=60)
        except (BrokenPipeError, Empty) as error:
            self.close()
            raise RuntimeError("METEOR 1.3 did not return a score") from error
        if response is None:
            raise RuntimeError("METEOR 1.3 exited before scoring the answer")
        return response

    def score(self, candidate, references):
        # Inputs are tokenized first, leaving the pipe delimiter unambiguous.
        fields = [" ".join(words) for words in [*references, candidate]]
        statistics = self.request(" ||| ".join(["SCORE", *fields]))
        return float(self.request("EVAL ||| " + statistics))

    def close(self):
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()


@lru_cache(maxsize=1)
def meteor():
    error = check_setup()
    if error:
        raise RuntimeError(error)
    return Meteor(metric_dir())


def messages(task):
    question = task["prompt"].split("\n\n", 1)[0]
    _, separator, summary = task["prompt"].partition("\n\n# Wikipedia plot summary\n\n")
    if not separator:
        raise ValueError(f"{task['key']}: missing the NarrativeQA summary")
    prompt = f"{summary}\n\nQuestion: {question}\n\nGive a short answer from the summary."
    return [{"role": "user", "content": prompt}]


def tokens(text):
    words = TOKENS.findall(text.strip().removesuffix("</s>").lower())
    return words[:-1] if words[-1:] == ["."] else words


def ngrams(words, size):
    return Counter(tuple(words[i:i + size]) for i in range(len(words) - size + 1))


def bleu_components(candidate, references):
    reference_length = min((len(ref) for ref in references), key=lambda n: (abs(n - len(candidate)), n))
    counts = []
    for size in range(1, 5):
        expected = ngrams(references[0], size) | ngrams(references[1], size)
        prediction = ngrams(candidate, size)
        counts.append((sum((prediction & expected).values()), sum(prediction.values())))
    return reference_length, counts


def bleu(length, reference_length, counts):
    if not length or any(not matches for matches, _ in counts):
        return 0.0
    brevity = min(0, 1 - reference_length / length)
    return math.exp(brevity + sum(math.log(matches / total) for matches, total in counts) / len(counts))


def lcs(left, right):
    row = [0] * (len(right) + 1)
    for token in left:
        previous, row = row, [0]
        for j, reference in enumerate(right):
            row.append(previous[j] + 1 if token == reference else max(previous[j + 1], row[j]))
    return row[-1]


def rouge_l(candidate, references):
    lengths = [lcs(candidate, reference) for reference in references]
    precision = max(length / len(candidate) for length in lengths)
    recall = max(length / len(ref) if ref else 0.0 for length, ref in zip(lengths, references))
    weight = 1.2 ** 2
    return (1 + weight) * precision * recall / (recall + weight * precision) if precision and recall else 0.0


def reference_output(task):
    return task["solution"].split("\n", 1)[0]


def score(task, output):
    candidate = tokens(output)
    if not candidate:
        return None
    references = [tokens(answer) for answer in task["solution"].split("\n")]
    reference_length, counts = bleu_components(candidate, references)
    with METEOR_LOCK:
        meteor_score = meteor().score(candidate, references)
    return {
        "sentence-bleu-1": bleu(len(candidate), reference_length, counts[:1]),
        "sentence-bleu-4": bleu(len(candidate), reference_length, counts),
        "meteor-1.3": meteor_score,
        "rouge-l": rouge_l(candidate, references),
    }
