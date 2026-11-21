"""Run the official calibrated BigCodeBench Instruct grader in its evaluation image."""

from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess
from uuid import uuid4


ATTEMPTS = 1
IMAGE = "benchopedia-bigcodebench:v0.2.4-pool-cleanup-1"
CAPTURE_FILES = ("dockerfile.eval",)
INPUTS_SHA256 = "81c918f4462d251f23d4f90a76dc3386b7cf3254a11bf2c05b2b81ae00b772d0"
BOSTON_SHA256 = "1df1f5ccfcd1cb9e8f9eaa2c871bb3355eafdde755267bcd593f817b21b92a7b"
BOSTON_TASK = "bigcodebench-0101"
NLTK_FIXTURES = {
    "corpora/stopwords.zip": "4491a6e09fee59f5f674edac3444305c9bfd2eb62b6873c835ce8f3805d95150",
    "corpora/words.zip": "54ed02917d6771dcc3e8141218960d020947f7f2ccfd9ac9b320979349746015",
    "sentiment/vader_lexicon.zip": "8adba4294eef3964d820bf655e37e61bdc3a341994356af59b74fb3b4a36ce5c",
    "taggers/averaged_perceptron_tagger.zip": "e1f13cf2532daadfd6f3bc481a49859f0b8ea6432ccdcd83e6a49a5f19008de9",
    "tokenizers/punkt.zip": "51c3078994aeaf650bfc8e028be4fb42b4a0d177d41c012b6a983979653660ec",
}
PREFIX = "Please provide a self-contained Python script that solves the following problem in a markdown code block:"
WORKER = """
import http.server
import json
import os
from pathlib import Path
import socketserver
import ssl
import subprocess
import sys
from threading import Thread
from bigcodebench.evaluate import check_correctness
from bigcodebench.sanitize import sanitize

fixture = Path('/opt/boston')
if fixture.is_file():
    class BostonData(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path != '/datasets/boston' or self.headers.get('Host') != 'lib.stat.cmu.edu':
                self.send_error(404)
                return
            body = fixture.read_bytes()
            self.send_response(200)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    server = http.server.HTTPServer(('127.0.0.1', 80), BostonData)
    Thread(target=server.serve_forever, daemon=True).start()

request = json.load(sys.stdin)
record = request["problem"]
if record["task_id"] == "BigCodeBench/314":
    # The test mocks the HTTP client, but the preparatory TLS socket is real.
    key = "/tmp/example-key.pem"
    cert = "/tmp/example-cert.pem"
    subprocess.run(["openssl", "req", "-x509", "-newkey", "ec", "-pkeyopt", "ec_paramgen_curve:P-256",
                    "-nodes", "-keyout", key, "-out", cert, "-days", "1",
                    "-subj", "/CN=www.example.com", "-addext", "subjectAltName=DNS:www.example.com"],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True, timeout=5)
    os.environ["SSL_CERT_FILE"] = cert
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert, key)
    tls = socketserver.TCPServer(("127.0.0.1", 443), socketserver.BaseRequestHandler)
    tls.socket = context.wrap_socket(tls.socket, server_side=True)
    Thread(target=tls.serve_forever, daemon=True).start()

code = sanitize(request["output"], entrypoint=record["entry_point"])
if not code.strip():
    verdict = "unparseable"
else:
    calibrated = request["code_prompt"] + "\\n    pass\\n" + code
    result = check_correctness(0, record, calibrated, max_as_limit=30 * 1024,
                               max_data_limit=30 * 1024, max_stack_limit=10,
                               min_time_limit=1, gt_time_limit=20)
    verdict = result["base"][0]
print("benchopedia-verdict:" + verdict)
"""


def inputs_path():
    root = next(p for p in Path(__file__).resolve().parents if (p / ".git").exists())
    return root / "build" / "bigcodebench-grading.json"


def boston_path():
    return inputs_path().with_name("bigcodebench-boston")


def nltk_path():
    return inputs_path().with_name("bigcodebench-nltk")


def matches_checksum(path, digest):
    return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest


@lru_cache(maxsize=1)
def check_setup():
    if not matches_checksum(inputs_path(), INPUTS_SHA256):
        return "Run python3 data/bigcodebench/setup_eval.py to install the pinned scoring inputs"
    if not matches_checksum(boston_path(), BOSTON_SHA256):
        return "Run python3 data/bigcodebench/setup_eval.py to install the pinned Boston housing data"
    nltk_root = nltk_path()
    if not (nltk_root / "tokenizers/punkt/PY3/english.pickle").is_file() or not all(
            matches_checksum(nltk_root / name, digest) for name, digest in NLTK_FIXTURES.items()):
        return "Run python3 data/bigcodebench/setup_eval.py to install the pinned NLTK data"
    try:
        state = subprocess.run(
            ["docker", "image", "inspect", "--format", '{{index .Config.Labels "org.benchopedia.bigcodebench-eval"}}', IMAGE],
            capture_output=True, text=True, timeout=10,
        )
        if state.returncode == 0 and state.stdout.strip() == IMAGE.split(":", 1)[1]:
            return None
    except (OSError, subprocess.TimeoutExpired):
        pass
    return "Start Docker and run python3 data/bigcodebench/setup_eval.py to build the evaluation image"


@lru_cache(maxsize=1)
def scoring_inputs():
    return json.loads(inputs_path().read_text(encoding="utf-8"))


def prompts(task):
    _, _, content = task["prompt"].partition("\n\n~~~python\n")
    complete, marker, instruct = content.partition("\n~~~\n\n## Instruct prompt\n\n~~~text\n")
    if not marker or not instruct.endswith("\n~~~"):
        raise ValueError(f"{task['key']}: missing a BigCodeBench prompt")
    return complete, instruct.removesuffix("\n~~~")


def messages(task):
    _, instruct = prompts(task)
    return [{"role": "user", "content": f"{PREFIX}\n{instruct.strip()}\n"}]


def reference_output(task):
    complete, _ = prompts(task)
    _, canonical_length = scoring_inputs()[task["key"]]
    return task["solution"][:len(complete) + 1 + canonical_length]


def grade(task, output):
    if not output.strip():
        return "unparseable", None
    code_prompt, _ = scoring_inputs()[task["key"]]
    ref = reference_output(task)
    problem = {
        "task_id": f"BigCodeBench/{int(task['key'].rsplit('-', 1)[1])}",
        "test": task["solution"][len(ref) + 1:],
        "entry_point": "task_func",
    }
    name = f"benchopedia-bigcode-{uuid4().hex}"
    fixture = ["--mount", f"type=bind,src={nltk_path()},dst=/opt/nltk_data,readonly",
               "-e", "NLTK_DATA=/opt/nltk_data"]
    if task["key"] == BOSTON_TASK:
        fixture.extend(["--add-host", "lib.stat.cmu.edu:127.0.0.1", "--mount",
                        f"type=bind,src={boston_path()},dst=/opt/boston,readonly"])
    if task["key"] == "bigcodebench-0176":
        fixture.extend(["--add-host", "dns.google:8.8.8.8", "--add-host", "dns.google:8.8.4.4"])
    if task["key"] == "bigcodebench-0314":
        fixture.extend(["--add-host", "www.example.com:127.0.0.1"])
    try:
        result = subprocess.run(
            ["docker", "run", "--rm", "--init", "--platform", "linux/amd64", "--name", name,
             "--pull=never", "--log-driver", "none", "--network", "none", "--read-only",
             "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--user", "65534:65534",
             "--memory", "4g", "--memory-swap", "4g", "--cpus", "2", "--pids-limit", "128",
             "--tmpfs", "/tmp:size=512m,mode=1777,exec,nosuid,nodev",
             "--tmpfs", "/nonexistent:size=128m,mode=1777,nosuid,noexec", *fixture, "--workdir", "/tmp",
             "-e", "MPLBACKEND=Agg", "-e", "MPLCONFIGDIR=/tmp/matplotlib", "-e", "XDG_CACHE_HOME=/tmp/cache",
             "-e", "OPENBLAS_NUM_THREADS=1", "--entrypoint", "python3",
             "-i", IMAGE, "-B", "-c", WORKER],
            input=json.dumps({"output": output, "problem": problem, "code_prompt": code_prompt}),
            capture_output=True, text=True, timeout=255,
        )
    except subprocess.TimeoutExpired:
        subprocess.run(["docker", "rm", "-f", name], capture_output=True, timeout=10)
        return "fail", "timed out"
    status = next((line.partition(":")[2] for line in reversed(result.stdout.splitlines())
                   if line.startswith("benchopedia-verdict:")), None)
    if result.returncode or status not in ("pass", "fail", "timeout", "unparseable"):
        raise RuntimeError(f"{task['key']}: BigCodeBench evaluator failed to report a verdict")
    if status == "unparseable":
        return "unparseable", None
    return ("pass" if status == "pass" else "fail"), status
