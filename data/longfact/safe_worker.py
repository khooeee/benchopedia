"""Run the pinned SAFE source with its HTTP exchanges supplied by the runner."""

from contextlib import redirect_stdout
import json
from pathlib import Path
import sys
from threading import Lock

import nltk
import openai
import requests


JUDGE = "https://api.openai.com/v1/chat/completions"
SEARCH = "https://google.serper.dev/search"
WIRE = sys.stdout
WIRE_LOCK = Lock()


def send(item):
    print(json.dumps(item, ensure_ascii=False), file=WIRE, flush=True)


def exchange(_session, method, url, **kwargs):
    if method.lower() == "post" and url == JUDGE and not kwargs.get("stream"):
        body = json.loads(kwargs["data"])
        if body["model"] != "gpt-3.5-turbo-0125":
            raise SystemExit("SAFE requested a different judge model")
        record = body | {"endpoint": url}
    elif method.lower() == "post" and url == SEARCH:
        record = {"endpoint": url, "params": kwargs["params"]}
    else:
        raise SystemExit("SAFE requested an unsupported network operation")
    with WIRE_LOCK:
        send({"request": record})
        payload = json.loads(sys.stdin.readline())
    response = requests.Response()
    response.status_code = 200
    response.headers["Content-Type"] = "application/json"
    response.encoding = "utf-8"
    response.url = url
    response._content = json.dumps(payload, ensure_ascii=False).encode()
    return response


def main():
    sys.path.insert(0, str(Path.cwd()))
    nltk.data.find("tokenizers/punkt/PY3/english.pickle")
    # The upstream import calls download even when the version is installed.
    nltk.download = lambda resource, **_: resource == "punkt"
    requests.Session.request = exchange
    openai.api_base = "https://api.openai.com/v1"

    from common import modeling, shared_config
    shared_config.openai_api_key = "benchopedia-transport"
    shared_config.serper_api_key = "benchopedia-transport"
    from eval import metric_utils
    from eval.safe import config, search_augmented_factuality_eval as safe

    if sys.argv[1:] == ["--check"]:
        return
    item = json.loads(sys.stdin.readline())
    rater = modeling.Model(config.model, temperature=config.model_temp, max_tokens=config.max_tokens)
    result = safe.main(prompt=item["prompt"], response=item["output"], rater=rater)
    supported = result[safe.SUPPORTED_LABEL]
    unsupported = result[safe.NOT_SUPPORTED_LABEL]
    scores = {"supported": supported, "not-supported": unsupported, "irrelevant": result[safe.IRRELEVANT_LABEL]}
    for k in (64, 178):
        scores[f"F1@{k}"] = metric_utils.calculate_metrics(supported, unsupported, max_claims=k)
    send({"scores": scores})


if __name__ == "__main__":
    with redirect_stdout(sys.stderr):
        main()
