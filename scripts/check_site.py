"""Check generated routes, anchors, data completeness, prompts, solutions and runs."""

import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

from helpers.build_sqlite import read_results
from helpers.site_path import output_path, site_url

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
        self.section_text = {}
        self.sections = []
        self.contents = []
        self.in_contents = False
        # Text of elements marked data-text, such as run commands, code and outputs.
        self.texts = {}
        self.reading_text = None
        self.results = []
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
        if "data-result" in attrs:
            self.results.append(attrs["data-result"])
        if "data-text" in attrs:
            self.reading_text = attrs["data-text"]
            self.texts[self.reading_text] = ""
        if tag == "section":
            self.section = attrs.get("id")
            if self.section:
                self.sections.append(self.section)
                self.section_links[self.section] = []
        if tag == "nav" and "toc" in attrs.get("class", "").split():
            self.in_contents = True
        if tag == "a" and self.in_contents:
            self.contents.append(attrs.get("href", ""))
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
        if self.reading_text:
            self.texts[self.reading_text] += data
        if self.section:
            self.section_text[self.section] = self.section_text.get(self.section, "") + data

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_contents = False
        if tag == "code":
            self.reading_solution = False
            self.reading_text = None
        if tag == "section":
            self.section = None


def main():
    pages = {p: Page(p.read_text()) for p in OUT.rglob("*.html")}
    assert pages, "Build the website first"
    errors = []
    catalog = pages[OUT / "index.html"]
    expected_flags = {}
    expected_tasks = {}
    guides = {}
    for metadata in (ROOT / "data").glob("*/benchmark.json"):
        benchmark = json.loads(metadata.read_text(encoding="utf-8"))
        expected_flags[benchmark["id"]] = str(bool(benchmark["has_solutions"])).lower()
        expected_tasks[benchmark["id"]] = str(bool(benchmark["task_count"])).lower()
        page = pages.get(OUT / "benchmarks" / benchmark["id"] / "index.html")
        assert page and "license" in page.sections, f"Missing License section: {benchmark['id']}"
        assert page.contents == [f"#{section}" for section in page.sections], f"Contents differ from sections: {benchmark['id']}"
        guides[benchmark["id"]] = page.section_text.get("how-to-run")
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
    # Each benchmark's search index is named after the benchmark it covers.
    tasks = [q | {"benchmark_id": path.stem}
             for path in (OUT / "assets/tasks").glob("*.json")
             for q in json.loads(path.read_text())]
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
    for benchmark_id, guide in guides.items():
        # The guide runs the benchmark's first task as its example.
        keys = sorted(task_key for owner, task_key in originals if owner == benchmark_id)
        if keys:
            assert guide and keys[0] in guide and "{{key}}" not in guide, f"How to run lacks its example task: {benchmark_id}"
        else:
            assert guide is None, f"How to run shown without tasks: {benchmark_id}"
    runs = check_runs(pages, tasks)
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"OK: {len(pages)} pages, all internal links/anchors, {len(tasks)} task routes, original prompts/solutions, environment/solution-source links and how-to-run guides, {runs} run(s)")


def page_for(pages, url):
    page = pages.get(OUT / output_path(site_url(url)) / "index.html")
    assert page, f"Missing page: {url}"
    return page


def check_runs(pages, tasks):
    """Each run's pages show its exact commands, code, results and graded outputs."""
    expected_status = {}
    run_dirs = sorted(p for p in (ROOT / "data").glob("*/runs/*") if p.is_dir())
    for run_dir in run_dirs:
        benchmark_id = run_dir.parent.parent.name
        run = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        results = sorted(read_results(run_dir), key=lambda r: r["key"])
        run_url = f"/benchmarks/{quote(benchmark_id, safe='')}/runs/{quote(run_dir.name, safe='')}/"
        page = page_for(pages, run_url)
        for number, command in enumerate(run["commands"], start=1):
            assert page.texts.get(f"command-{number}") == command["command"], f"Command {number} differs: {run_url}"
        code_dir = run_dir / "code"
        for path in (p for p in code_dir.rglob("*") if p.is_file()):
            name = path.relative_to(code_dir).as_posix()
            assert page.texts.get(f"file:{name}") == path.read_text(encoding="utf-8"), f"Code differs: {run_url} {name}"
        assert page.results == [r["result"] for r in results], f"Task results differ: {run_url}"
        for result in results:
            task_page = page_for(pages, run_url + f"tasks/{quote(result['key'], safe='')}/")
            assert task_page.results == [result["result"]], f"Result differs: {run_url} {result['key']}"
            for attempt in result["attempts"]:
                assert task_page.texts.get(f"output-{attempt['number']}") == attempt["output"], \
                    f"Output differs: {run_url} {result['key']} attempt {attempt['number']}"
            key = (benchmark_id, result["key"])
            if result["result"] == "pass" or expected_status.get(key) != "solved":
                expected_status[key] = "solved" if result["result"] == "pass" else "open"
        benchmark_page = page_for(pages, f"/benchmarks/{quote(benchmark_id, safe='')}/")
        assert "results" in benchmark_page.sections, f"Missing Results section: {benchmark_id}"
    benchmarks_with_runs = {run_dir.parent.parent.name for run_dir in run_dirs}
    for q in tasks:
        key = (q["benchmark_id"], q["key"])
        expected = expected_status.get(key, "untested") if q["benchmark_id"] in benchmarks_with_runs else None
        assert q.get("status") == expected, f"Status differs: {key}"
        if expected:
            assert "results" in pages[OUT / output_path(q["url"]) / "index.html"].sections, f"Missing Results section: {key}"
    return len(run_dirs)


if __name__ == "__main__":
    main()
