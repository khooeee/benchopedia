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
        self.section = None
        self.section_links = {}
        self.sections = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "section":
            self.section = attrs.get("id")
            if self.section:
                self.sections.append(self.section)
                self.section_links[self.section] = []
        if tag == "a" and self.section:
            self.section_links[self.section].append(attrs.get("href", ""))
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
        if tag == "section":
            self.section = None


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
        # JSONL records are separated by LF, not Unicode separators that can
        # legitimately appear inside imported text (including MMLU prompts).
        with path.open(encoding="utf-8") as stream:
            for line in stream:
                task = json.loads(line)
                key = (path.parent.name, task["key"])
                assert key not in originals, f"Duplicate task identifier: {key}"
                originals[key] = task
    assert len(tasks) == len(originals), "Search index is incomplete"
    for q in tasks:
        key = (q["benchmark_id"], q["key"])
        assert q["prompt"] == originals[key]["prompt"], f"Search prompt changed: {key}"
        task_dir = OUT / q["url"].lstrip("/")
        assert (task_dir / "index.html").exists(), f"Missing task page: {key}"
        assert pages[task_dir / "index.html"].solution == originals[key].get("solution"), f"Solution changed: {key}"
        page = pages[task_dir / "index.html"]
        assert q.get("prompt_source_url") == originals[key].get("prompt_source_url"), f"Search prompt source changed: {key}"
        if originals[key].get("prompt_source_url"):
            assert originals[key]["prompt_source_url"] in page.section_links.get("task-prompt", []), f"Missing prompt source: {key}"
        if originals[key].get("environment_url"):
            assert originals[key]["environment_url"] in page.section_links.get("environment", []), f"Missing environment link: {key}"
            assert page.sections.index("environment") < page.sections.index("task-prompt"), f"Environment must precede Task Prompt: {key}"
        if originals[key].get("solution_source_url"):
            assert originals[key]["solution_source_url"] in page.section_links.get("solution", []), f"Missing solution source: {key}"
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"OK: {len(pages)} pages, all internal links/anchors, {len(tasks)} task routes, original prompts/solutions and environment/solution-source links")


if __name__ == "__main__":
    main()
