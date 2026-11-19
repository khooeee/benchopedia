"""Ollama's HTTP API, called with Python's standard library.

https://github.com/ollama/ollama/blob/main/docs/api.md
"""

import json
import sys
import time
import urllib.error
import urllib.request

URL = "http://localhost:11434"
# A thinking model can write 81,920 tokens before answering, and a non-streaming
# request sends nothing until it finishes.
TIMEOUT_SECONDS = 4 * 60 * 60
# Waits before each retry of a request that failed without a response from the model.
RETRY_WAITS = (5, 30, 120, 300)


def get(path):
    with urllib.request.urlopen(URL + path, timeout=30) as response:
        return json.load(response)


def version():
    return get("/api/version")["version"]


def digest(provider_model):
    """The digest Ollama reports for its local copy of the model, which pins its weights."""
    for model in get("/api/tags")["models"]:
        if model["name"] == provider_model:
            return "sha256:" + model["digest"]
    raise SystemExit(f"Ollama has no model {provider_model}; run: ollama pull {provider_model}")


def chat(provider_model, messages, profile, seed):
    """Send one chat request and wait for the whole response.

    Returns (request, response, latency_ms, output): the exact request body, the
    parsed response body, the wall-clock time the request took, and the model's
    final text, without its reasoning.
    """
    request = {
        "model": provider_model,
        "messages": messages,
        "stream": False,
        "think": profile["think"],
        "options": profile["options"] | {"seed": seed},
    }
    body = json.dumps(request).encode("utf-8")
    for wait in RETRY_WAITS + (None,):
        started = time.monotonic()
        try:
            http_request = urllib.request.Request(URL + "/api/chat", data=body,
                                                  headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(http_request, timeout=TIMEOUT_SECONDS) as http_response:
                response = json.load(http_response)
            break
        except (urllib.error.URLError, ConnectionError, TimeoutError) as error:
            if wait is None:
                raise
            print(f"Ollama request failed ({error}); retrying in {wait}s", file=sys.stderr, flush=True)
            time.sleep(wait)
    latency_ms = round((time.monotonic() - started) * 1000)
    if not response.get("done"):
        raise RuntimeError(f"Ollama returned an unfinished response: {response}")
    return request, response, latency_ms, response["message"]["content"]
