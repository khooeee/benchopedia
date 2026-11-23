"""Call the dated OpenAI judge used by the pinned simple-evals harness."""

import json
import os
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CHAT_URL = "https://api.openai.com/v1/chat/completions"


def setup_error():
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        return "Set OPENAI_API_KEY for the pinned simple-evals judge."


def request_body(model, messages):
    return {"model": model, "messages": messages, "temperature": 0.5, "max_tokens": 2048}


def chat(model, messages):
    error = setup_error()
    if error:
        raise RuntimeError(error)
    request = request_body(model, messages)
    http_request = Request(
        CHAT_URL, data=json.dumps(request).encode("utf-8"),
        headers={"Authorization": f"Bearer {os.environ['OPENAI_API_KEY'].strip()}",
                 "Content-Type": "application/json"},
    )
    started = time.monotonic()
    try:
        with urlopen(http_request, timeout=120) as response_file:
            response = json.load(response_file)
    except HTTPError as error:
        raise RuntimeError(f"The simple-evals judge returned HTTP {error.code}") from None
    except (URLError, TimeoutError, json.JSONDecodeError) as error:
        raise RuntimeError(f"The simple-evals judge request failed ({type(error).__name__})") from None
    elapsed_ms = round((time.monotonic() - started) * 1000)
    if response.get("model") != model:
        raise RuntimeError("The simple-evals judge did not serve the pinned model.")
    try:
        output = response["choices"][0]["message"]["content"]
    except (IndexError, KeyError, TypeError):
        output = None
    if not isinstance(output, str):
        raise RuntimeError("The simple-evals judge returned no text.")
    return request, response, elapsed_ms, output
