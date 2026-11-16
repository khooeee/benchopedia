"""Check generated routes, anchors, data completeness, prompts and solutions."""

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist"


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.ids = set()
        self.title = False
        self.solution = None
        self.reading_solution = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag in ("a", "link", "script"):
            self.links.append(attrs.get("href", attrs.get("src", "")))
        if tag == "title":
            self.title = True
        if tag == "code" and attrs.get("id") == "solution-text":
            self.solution = ""
            self.reading_solution = True

    def handle_data(self, data):
        if self.reading_solution:
            self.solution += data

    def handle_endtag(self, tag):
        if tag == "code":
            self.reading_solution = False


def main():
    pages = {p: Page(p.read_text()) for p in OUT.rglob("*.html")}
    assert pages, "Build the website first"
    errors = []
    for path, page in pages.items():
        if not page.title:
            errors.append(f"{path}: missing title")
        for href in page.links:
            url = urlsplit(href)
            if url.scheme or url.netloc or not href:
                continue
            target = OUT / url.path.lstrip("/") if url.path.startswith("/") else path.parent / url.path
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                errors.append(f"{path}: missing {href}")
            elif url.fragment and target in pages and url.fragment not in pages[target].ids:
                errors.append(f"{path}: missing anchor {href}")
    tasks = json.loads((OUT / "assets/tasks.json").read_text())
    originals = {}
    for path in (ROOT / "data").glob("*/tasks.jsonl"):
        for line in path.read_text().splitlines():
            task = json.loads(line)
            originals[(path.parent.name, task["key"])] = task
    assert len(tasks) == len(originals), "Search index is incomplete"
    for q in tasks:
        key = (q["benchmark_id"], q["key"])
        assert q["prompt"] == originals[key]["prompt"], f"Search prompt changed: {key}"
        task_dir = OUT / q["url"].lstrip("/")
        assert (task_dir / "index.html").exists(), f"Missing task page: {key}"
        # The raw prompt must round-trip through the inert JSON script.
        text = (task_dir / "index.html").read_text()
        embedded = text.split('<script type="application/json" id="prompt-data">', 1)[1].split('</script>', 1)[0]
        assert json.loads(embedded) == originals[key]["prompt"], f"Copy prompt changed: {key}"
        assert pages[task_dir / "index.html"].solution == originals[key].get("solution"), f"Solution changed: {key}"
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"OK: {len(pages)} pages, all internal links/anchors, {len(tasks)} task routes and exact original prompts/solutions")


if __name__ == "__main__":
    main()
