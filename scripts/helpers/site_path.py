"""Map public URLs to the configured static-site mount path."""

import os
import re

BASE_PATH = os.environ.get("BENCHOPEDIA_BASE_PATH", "").rstrip("/")
if not re.fullmatch(r"(?:/[A-Za-z0-9._~-]+)*", BASE_PATH):
    raise ValueError("BENCHOPEDIA_BASE_PATH must be a path such as /benchopedia")
if any(part in (".", "..") for part in BASE_PATH.split("/")):
    raise ValueError("BENCHOPEDIA_BASE_PATH cannot contain dot segments")


def site_url(path):
    return BASE_PATH + path


def output_path(url):
    prefix = BASE_PATH + "/"
    if not url.startswith(prefix):
        raise ValueError(f"URL is outside the site base path: {url}")
    return url[len(prefix):]
