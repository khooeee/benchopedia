"""Check generated routes, anchors, data completeness, prompts and solutions."""

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from helpers.site_path import output_path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist"


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.ids = set()
        self.title = False
        self.benchmarks = {}
        self.solution_filter = False
        self.task_filter = False
        self.benchmark_tasks = {}
        self.solution = None
        self.reading_solution = False
        self.section = None
        self.section_links = {}
        self.sections = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "data-benchmark" in attrs:
            self.benchmarks[attrs["data-benchmark"]] = attrs.get("data-has-solutions")
            self.benchmark_tasks[attrs["data-benchmark"]] = attrs.get("data-has-tasks")
        if tag == "input" and attrs.get("id") == "filter-solutions":
            self.solution_filter = (attrs.get("type") == "checkbox"
                                    and attrs.get("name") == "has_solutions"
                                    and attrs.get("value") == "1")
        if tag == "input" and attrs.get("id") == "filter-tasks":
            self.task_filter = (attrs.get("type") == "checkbox"
                                and attrs.get("name") == "has_tasks"
                                and attrs.get("value") == "1")
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
    catalog = pages[OUT / "index.html"]
    expected_flags = {}
    expected_tasks = {}
    for metadata in (ROOT / "data").glob("*/benchmark.json"):
        benchmark = json.loads(metadata.read_text(encoding="utf-8"))
        expected_flags[benchmark["id"]] = str(bool(benchmark["has_solutions"])).lower()
        expected_tasks[benchmark["id"]] = str(bool(benchmark["task_count"])).lower()
        page = pages.get(OUT / "benchmarks" / benchmark["id"] / "index.html")
        assert page and "license" in page.sections, f"Missing License section: {benchmark['id']}"
    assert catalog.benchmarks == expected_flags, "Catalog solution flags differ from metadata"
    assert catalog.solution_filter, "Missing benchmark solutions checkbox"
    assert catalog.benchmark_tasks == expected_tasks, "Catalog task flags differ from metadata"
    assert catalog.task_filter, "Missing benchmark tasks checkbox"
    for path, page in pages.items():
        if not page.title:
            errors.append(f"{path}: missing title")
        for href in page.links:
            url = urlsplit(href)
            if url.scheme or url.netloc or not href:
                continue
            target = OUT / output_path(url.path) if url.path.startswith("/") else path.parent / unquote(url.path)
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
        task_dir = OUT / output_path(q["url"])
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
