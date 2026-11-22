"""OpenRouter chat completions and free-model quota checks."""

import json
import os
from pathlib import Path
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
KEY_URL = "https://openrouter.ai/api/v1/key"
ENV_FILE = Path(__file__).resolve().parents[1] / ".env"
FREE_INTERVAL = 3.1
free_request_lock = threading.Lock()
next_free_request = 0.0


class RateLimited(RuntimeError):
    def __init__(self, error):
        try:
            metadata = json.load(error).get("error", {}).get("metadata") or {}
        except (ValueError, AttributeError):
            metadata = {}
        self.daily = metadata.get("limit_source") == "openrouter_free_tier_daily"
        retry_after = error.headers.get("Retry-After", "") if error.headers else ""
        self.retry_after = int(retry_after) if retry_after.isascii() and retry_after.isdigit() else None
        super().__init__("OpenRouter daily free-model quota exhausted" if self.daily
                         else "OpenRouter returned HTTP 429")


def api_key():
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if key:
        return key
    if ENV_FILE.is_file():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            name, separator, value = line.strip().removeprefix("export ").partition("=")
            if separator and name.strip() == "OPENROUTER_API_KEY":
                key = value.strip().strip("'\"")
    if not key:
        raise SystemExit("Set OPENROUTER_API_KEY in the repository's .env file or process environment.")
    return key


def request_json(request, timeout):
    try:
        with urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except HTTPError as error:
        if error.code == 429:
            raise RateLimited(error) from None
        raise RuntimeError(f"OpenRouter returned HTTP {error.code}") from None
    except (URLError, TimeoutError) as error:
        raise RuntimeError(f"OpenRouter connection failed ({type(error).__name__})") from None
    except json.JSONDecodeError:
        raise RuntimeError("OpenRouter returned invalid JSON") from None


def free_requests_remaining():
    request = Request(KEY_URL, headers={"Authorization": f"Bearer {api_key()}"})
    data = request_json(request, timeout=15)["data"]
    quota = data.get("free_model_daily_requests") or {}
    remaining = quota.get("remaining")
    if type(remaining) is not int or remaining < 0:
        raise RuntimeError("OpenRouter did not report a daily free-model quota for this key")
    return remaining


def chat(provider_model, messages, profile, seed):
    global next_free_request
    request = profile["options"] | {
        "model": provider_model,
        "messages": messages,
        "stream": False,
        "seed": seed,
    }
    headers = {
        "Authorization": f"Bearer {api_key()}",
        "Content-Type": "application/json",
    }
    http_request = Request(CHAT_URL, data=json.dumps(request).encode("utf-8"), headers=headers)
    if provider_model.endswith(":free"):
        with free_request_lock:
            wait = next_free_request - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            next_free_request = time.monotonic() + FREE_INTERVAL
    started = time.monotonic()
    response = request_json(http_request, timeout=300)
    elapsed_ms = round((time.monotonic() - started) * 1000)
    choices = response.get("choices")
    if not choices or choices[0].get("error") or response.get("error"):
        raise RuntimeError("OpenRouter returned no successful chat choice")
    output = choices[0]["message"].get("content") or ""
    if not isinstance(output, str):
        raise RuntimeError("OpenRouter returned non-text content")
    return request, response, elapsed_ms, output


if __name__ == "__main__":
    try:
        print(free_requests_remaining())
    except RuntimeError as error:
        raise SystemExit(str(error)) from None
