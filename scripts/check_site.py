"""Check generated routes, anchors, data completeness and prompt fidelity."""

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
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag in ("a", "link", "script"):
            self.links.append(attrs.get("href", attrs.get("src", "")))
        if tag == "title":
            self.title = True


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
    questions = json.loads((OUT / "assets/questions.json").read_text())
    originals = {}
    for path in (ROOT / "data").glob("*/questions.jsonl"):
        for line in path.read_text().splitlines():
            question = json.loads(line)
            originals[(path.parent.name, question["key"])] = question["prompt"]
    assert len(questions) == len(originals), "Search index is incomplete"
    for q in questions:
        key = (q["benchmark_id"], q["key"])
        assert q["prompt"] == originals[key], f"Search prompt changed: {key}"
        question_dir = OUT / q["url"].lstrip("/")
        assert (question_dir / "index.html").exists(), f"Missing question page: {key}"
        # The raw prompt must round-trip through the inert JSON script.
        text = (question_dir / "index.html").read_text()
        embedded = text.split('<script type="application/json" id="prompt-data">', 1)[1].split('</script>', 1)[0]
        assert json.loads(embedded) == originals[key], f"Copy prompt changed: {key}"
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"OK: {len(pages)} pages, all internal links/anchors, {len(questions)} question routes and exact original prompts")


if __name__ == "__main__":
    main()
