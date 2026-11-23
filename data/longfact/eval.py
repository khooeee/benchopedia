"""Grade LongFact with the pinned SAFE evaluator and replayable API requests."""

import json
import os
from pathlib import Path
import subprocess
from tempfile import TemporaryFile
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener


ATTEMPTS = 1
MODEL_OPTIONS = {"temperature": 0, "max_tokens": 1024}
CAPTURE_FILES = ("safe_worker.py", "setup_eval.py", "safe-requirements.txt")
POSTAMBLE = ("Provide as many specific details and examples as possible (such as names of "
             "people, numbers, events, locations, dates, times, etc.)")
REVISION = "9d27158d198ced0a9d8271a80147cae580614601"
JUDGE = "https://api.openai.com/v1/chat/completions"
SEARCH = "https://google.serper.dev/search"


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def runtime():
    root = next(path for path in Path(__file__).resolve().parents if (path / ".git").exists())
    return root / "build" / "longfact-safe" / REVISION


def check_runtime():
    location = runtime()
    marker = location / "ready"
    if (not marker.is_file() or marker.read_text().strip() != REVISION
            or not (location / "venv/bin/python").is_file() or not (location / "upstream").is_dir()):
        return "Run python3 data/longfact/setup_eval.py to install the pinned SAFE runtime."


def check_setup():
    missing = [key for key in ("OPENAI_API_KEY", "SERPER_API_KEY") if not os.environ.get(key, "").strip()]
    problems = [f"Set {' and '.join(missing)} for the pinned SAFE judge and search backend."] if missing else []
    if error := check_runtime():
        problems.append(error)
    return " ".join(problems) or None


def messages(task):
    return [{"role": "user", "content": f"{task['prompt']} {POSTAMBLE}".strip(" \n")}]


def scorer_request(request):
    endpoint = request["endpoint"]
    if endpoint == JUDGE:
        body = {key: value for key, value in request.items() if key != "endpoint"}
        headers = {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY'].strip()}"}
        data = json.dumps(body).encode()
    elif endpoint == SEARCH:
        endpoint += "?" + urlencode(request["params"])
        headers = {"X-API-KEY": os.environ["SERPER_API_KEY"].strip()}
        data = None
    else:
        raise ValueError("Unexpected SAFE endpoint")
    headers["Content-Type"] = "application/json"
    opener = build_opener(NoRedirect)
    try:
        with opener.open(Request(endpoint, data=data, headers=headers, method="POST"), timeout=60) as response:
            result = json.load(response)
    except HTTPError as error:
        raise RuntimeError(f"SAFE service returned HTTP {error.code} for {request['endpoint']}") from None
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"SAFE service request failed for {request['endpoint']} ({type(error).__name__})") from None
    if not isinstance(result, dict):
        raise RuntimeError(f"SAFE service returned an invalid response for {request['endpoint']}")
    if request["endpoint"] == JUDGE and result.get("model") != request["model"]:
        raise RuntimeError("The SAFE judge did not serve the dated model")
    return result


def score_with_calls(task, output, request):
    error = check_runtime()
    if error:
        raise RuntimeError(error)
    location = runtime()
    worker = Path(__file__).with_name("safe_worker.py").resolve()
    env = os.environ | {"NLTK_DATA": str(location / "nltk_data"), "PYTHONHASHSEED": "0"}
    # The subprocess uses placeholders. Only the runner's transport reads the keys.
    for key in ("OPENAI_API_KEY", "SERPER_API_KEY"):
        env.pop(key, None)
    args = [str(location / "venv/bin/python"), str(worker)]
    with TemporaryFile() as logs, subprocess.Popen(
        args, cwd=location / "upstream", env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=logs, text=True, encoding="utf-8",
    ) as process:
        try:
            process.stdin.write(json.dumps({"prompt": messages(task)[0]["content"], "output": output}) + "\n")
            process.stdin.flush()
            for line in process.stdout:
                item = json.loads(line)
                if "scores" in item:
                    process.stdin.close()
                    if process.wait():
                        break
                    return item["scores"]
                response = request(item["request"])
                process.stdin.write(json.dumps(response, ensure_ascii=False) + "\n")
                process.stdin.flush()
        except BaseException:
            if process.poll() is None:
                process.kill()
            raise
        logs.seek(0, 2)
        logs.seek(max(0, logs.tell() - 4000))
        raise RuntimeError("SAFE worker exited without a score.\n" + logs.read().decode("utf-8", "replace"))
