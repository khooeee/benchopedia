"""Generate the complete static encyclopedia from the validated SQLite database.

Run `python3 scripts/build_site.py`; no third-party packages are required.
"""

import html
import json
import re
import shutil
import sqlite3
from pathlib import Path
from urllib.parse import quote

from helpers.build_sqlite import main as build_sqlite
from helpers.site_path import BASE_PATH, output_path, site_url

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist"


def esc(value):
    return html.escape(str(value), quote=True)


def inline(text):
    """A small, escaped Markdown subset; upstream HTML is always inert."""
    tokens = []

    def save(markup):
        tokens.append(markup)
        return f"\x00{len(tokens) - 1}\x00"

    text = re.sub(r"`([^`\n]+)`", lambda m: save(f"<code>{esc(m[1])}</code>"), text)
    text = re.sub(r"\[([^\]\n]+)\]\((https?://[^\s)]+)\)",
                  lambda m: save(f'<a href="{esc(m[2])}" rel="noreferrer">{esc(m[1])}</a>'), text)
    text = esc(text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
    return re.sub(r"\x00(\d+)\x00", lambda m: tokens[int(m[1])], text)


def markdown(text):
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S).replace("\r\n", "\n")
    blocks, paragraph, code = [], [], []
    in_code = False
    fence = ""

    def flush():
        if paragraph:
            blocks.append("<p>" + inline("\n".join(paragraph)) + "</p>")
            paragraph.clear()

    for line in text.splitlines():
        match = re.match(r"^\s*(`{3,}|~{3,})(.*)$", line)
        if match and (not in_code or match[1].startswith(fence[0])):
            flush()
            if in_code:
                blocks.append("<pre><code>" + esc("\n".join(code)) + "</code></pre>")
                code.clear()
            else:
                fence = match[1]
            in_code = not in_code
        elif in_code:
            code.append(line)
        elif not line.strip():
            flush()
        elif re.match(r"^#{1,6}\s", line):
            flush()
            blocks.append("<h3>" + inline(re.sub(r"^#+\s*", "", line)) + "</h3>")
        elif re.match(r"^\s*[-*]\s+", line):
            flush()
            blocks.append('<p class="list-line">• ' + inline(re.sub(r"^\s*[-*]\s+", "", line)) + "</p>")
        elif line.startswith("> "):
            flush()
            blocks.append("<blockquote>" + inline(line[2:]) + "</blockquote>")
        else:
            paragraph.append(line)
    flush()
    if code:
        blocks.append("<pre><code>" + esc("\n".join(code)) + "</code></pre>")
    return "\n".join(blocks)


def task_title(prompt):
    for line in re.sub(r"<!--.*?-->", "", prompt, flags=re.S).splitlines():
        line = line.strip().lstrip("# ")
        if line:
            return line.replace("`", "")[:220]
    return "Untitled task"


def task_url(q):
    return f'/benchmarks/{quote(q["benchmark_id"], safe="")}/tasks/{quote(q["key"], safe="")}/'


def benchmark_url(b):
    return f'/benchmarks/{quote(b["id"], safe="")}/'


def tasks_url(b):
    return benchmark_url(b) + 'tasks/'


def all_tasks_url(b):
    # A sibling of tasks/ so it can never collide with a task key.
    return benchmark_url(b) + 'all-tasks/'


def write(path, content):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")



def layout(title, body, active="benchmarks", description="Descriptions, datasets, and tasks for AI benchmarks."):
    def nav(key, url, label):
        current = ' aria-current="page"' if active == key else ''
        return f'<a href="{url}"{current}>{label}</a>'

    page = f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="site-base-path" content="{esc(BASE_PATH)}">
<title>{esc(title)} · Benchopedia</title><meta name="description" content="{esc(description)}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/style.css"><script src="/assets/app.js" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="header-inner"><a class="site-name" href="/">Benchopedia</a><span class="site-description">The AI benchmark encyclopedia</span>
<nav aria-label="Main navigation">{nav('benchmarks','/','Benchmarks')} <span aria-hidden="true">|</span> {nav('about','/about/','About')}</nav></div></header>
<main id="main" tabindex="-1">{body}</main>
<footer><a href="/about/">About Benchopedia</a> · <a href="https://github.com/khooeee/benchopedia/issues">Corrections &amp; suggestions</a></footer>
</body></html>'''
    return re.sub(r'(href|src)="(/(?!/)[^"]*)"',
                  lambda match: f'{match[1]}="{site_url(match[2])}"', page)


def task_list(rows, start=1):
    entries = []
    for q in rows:
        url = task_url(q)
        entries.append(f'''<li><div class="entry-links"><a href="{url}">{esc(q['key'])}</a></div>
<div class="entry-title"><a href="{url}">{esc(q['title'])}</a></div></li>''')
    return f'<ol class="entry-list" start="{start}">' + ''.join(entries) + '</ol>'


def task_count_label(b):
    # A null count means data/<id>/exclusions.md leaves the tasks out.
    return f"{b['task_count']:,}" if b['task_count'] else 'not included'


def home():
    ordered = sorted(BENCHMARKS, key=lambda b: (b['released_on'],b['name']), reverse=True)
    groups = []
    for year in sorted({b['released_on'][:4] for b in ordered}, reverse=True):
        entries = []
        for b in (b for b in ordered if b['released_on'].startswith(year)):
            url = benchmark_url(b)
            task_link = f'<a href="{tasks_url(b)}">tasks</a> · ' if b['task_count'] else ''
            entries.append(f'''<li data-benchmark="{esc(b['id'])}" data-has-tasks="{str(bool(b['task_count'])).lower()}" data-has-solutions="{str(bool(b['has_solutions'])).lower()}" data-search="{esc((b['name']+' '+b['id']+' '+b['summary']).lower())}">
<div class="entry-title"><a href="{url}">{esc(b['name'])}</a></div>
<div class="entry-links">{task_link}<a href="{esc(b['homepage_url'])}">website</a> · <a href="{esc(b['dataset_url'])}">dataset</a></div>
<p class="entry-summary">{esc(b['summary'])}</p>
<div class="entry-meta">Released: {esc(b['released_on'])} · Tasks: {task_count_label(b)}</div></li>''')
        groups.append(f'<section class="year-group"><h2>{year}</h2><ol class="entry-list">' + ''.join(entries) + '</ol></section>')
    body = f'''<h1>Benchmarks</h1>
<form class="search-form" role="search"><label for="benchmark-search">Search:</label> <input type="search" id="benchmark-search" name="q" placeholder="Name or description"> <button type="submit">Search</button> <label class="benchmark-filter"><input type="checkbox" id="filter-tasks" name="has_tasks" value="1"> Has tasks</label> <label class="benchmark-filter"><input type="checkbox" id="filter-solutions" name="has_solutions" value="1"> Has solutions</label></form>
<p class="list-summary"><span id="benchmark-count" role="status" aria-live="polite">{len(BENCHMARKS)} benchmark{'s' if len(BENCHMARKS)!=1 else ''}</span></p>
<div id="catalog">{''.join(groups)}</div><div id="benchmark-empty" hidden><p>No benchmarks match your search.</p><button type="button" id="reset-benchmarks">Clear filters</button></div>'''
    write('index.html',layout('Benchmarks',body))


def benchmark_page(b):
    facts = [('Released',b['released_on']),('Tasks',task_count_label(b))]
    if b['task_count']:
        task_link = f'<a href="{tasks_url(b)}">browse {b["task_count"]:,} tasks</a> · '
        dataset = f'''<p>{b['task_count']:,} tasks in this snapshot. <a href="{tasks_url(b)}">Browse tasks</a> or visit <a href="{esc(b['dataset_url'])}">the upstream dataset</a>.</p>'''
    else:
        task_link = ''
        dataset = f'''<p>Benchopedia does not include this benchmark's tasks; the <a href="#license">License</a> section explains why. Visit <a href="{esc(b['dataset_url'])}">the upstream dataset</a> for the tasks.</p>'''
    sources = json.loads(b['sources'])
    source_list = ''.join(f'<li><a href="{esc(s["url"])}">{esc(s["title"])}</a></li>' for s in sources)
    # The review's own title would duplicate the section heading.
    license_text = re.sub(r"\A# [^\n]*\n", "", b['redistribution_review'])
    body = f'''<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Benchmarks</a> &gt; {esc(b['name'])}</nav>
<h1>{esc(b['name'])}</h1><p class="resource-links">[{task_link}<a href="{esc(b['homepage_url'])}">official website</a> · <a href="{esc(b['dataset_url'])}">dataset</a>]</p>
<p>{esc(b['summary'])}</p><dl class="metadata">{''.join(f'<div><dt>{esc(k)}:</dt><dd>{esc(v)}</dd></div>' for k,v in facts)}</dl>
<article class="prose"><section id="overview"><h2>Overview</h2>{markdown(b['overview'])}</section>
<section id="methodology"><h2>Methodology</h2>{markdown(b['methodology'])}</section>
<section id="scoring"><h2>Scoring</h2>{markdown(b['scoring'])}</section>
<section id="dataset"><h2>Dataset</h2>{dataset}</section>
<section id="limitations"><h2>Limitations</h2>{markdown(b['limitations'])}</section>
<section id="license"><h2>License</h2>{markdown(license_text)}</section>
<section id="sources"><h2>Sources</h2><ol>{source_list}</ol><details class="snapshot"><summary>Dataset revision</summary><p>Snapshot of <a href="{esc(b['dataset_url'])}">the upstream dataset</a> at revision <code>{esc(b['dataset_revision'])}</code>.</p></details></section></article>'''
    write(f'benchmarks/{b["id"]}/index.html',layout(b['name'],body,description=b['summary']))


def library(b, rows):
    """One benchmark's searchable task list, its one-page fallback and search index."""
    crumbs = f'<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Benchmarks</a> &gt; <a href="{benchmark_url(b)}">{esc(b["name"])}</a> &gt; Tasks</nav>'
    body = f'''{crumbs}<h1>{esc(b['name'])} tasks</h1>
<section class="task-library" aria-label="Browse tasks" data-benchmark-id="{esc(b['id'])}"><div class="search-form" role="search"><label for="task-search">Search:</label> <input type="search" id="task-search" placeholder="Task text or task ID"></div>
<div class="library-summary"><p id="task-count" role="status" aria-live="polite">1–{min(25,len(rows))} of {len(rows):,} tasks</p></div>
<nav class="pagination" aria-label="Task pages"><button type="button" id="page-prev" disabled>Previous</button> <span id="page-status">Page 1 of {max(1,(len(rows)+24)//25)}</span> <button type="button" id="page-next">Next</button></nav>
<div id="task-results">{task_list(rows[:25])}</div><div id="task-empty" hidden><p>No tasks match your search.</p><button type="button" data-clear-tasks>Clear search</button></div>
<p class="all-tasks-link"><a href="{all_tasks_url(b)}">View all {len(rows):,} tasks on one page</a></p><noscript><p>Search requires JavaScript. Use the complete task index above to browse without it.</p></noscript></section>'''
    write(output_path(site_url(tasks_url(b)))+'index.html',layout(f"{b['name']} tasks",body))
    all_body = f'{crumbs}<h1>All {esc(b["name"])} tasks</h1><p><a href="{tasks_url(b)}">Search tasks</a></p>'+task_list(rows)
    write(output_path(site_url(all_tasks_url(b)))+'index.html',layout(f"All {b['name']} tasks",all_body))
    search_data = [{k:q[k] for k in ('key','title','prompt','prompt_source_url')} | {'url':site_url(task_url(q))} for q in rows]
    write(f'assets/tasks/{b["id"]}.json',json.dumps(search_data,ensure_ascii=False,separators=(',',':')))


def task_page(q, previous, following):
    b = next(b for b in BENCHMARKS if b['id']==q['benchmark_id'])
    prev_link = f'<a href="{task_url(previous)}">Previous task</a>' if previous else '<span></span>'
    next_link = f'<a href="{task_url(following)}">Next task</a>' if following else '<span></span>'
    prompt_source = f'<p><a href="{esc(q["prompt_source_url"])}">Source</a></p>' if q.get('prompt_source_url') else ''
    environment_section = ''
    if q.get('environment_url'):
        environment_section = f'<section id="environment" aria-label="Environment"><p><a href="{esc(q["environment_url"])}">Environment</a></p></section>'
    solution_source = f'<p><a href="{esc(q["solution_source_url"])}">Source</a></p>' if q.get('solution_source_url') else ''
    solution_content = ''
    if q.get('solution') is not None:
        solution_content = f'<details><summary>Show reference solution</summary><pre><code id="solution-text">{esc(q["solution"])}</code></pre></details>'
    solution_section = ''
    if solution_source or solution_content:
        solution_section = f'<section id="solution"><h2>Solution</h2>{solution_content}{solution_source}</section>'
    how_to_run = b['how_to_run_html'].replace('{{key}}', esc(q['key']))
    body = f'''<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Benchmarks</a> &gt; <a href="{benchmark_url(b)}">{esc(b['name'])}</a> &gt; <a href="{tasks_url(b)}">Tasks</a></nav>
<p class="task-id">{esc(q['key'])}</p><h1>{esc(q['title'])}</h1>
<article class="prose">{environment_section}<section id="task-prompt"><h2>Task Prompt</h2><div class="prompt-content">{markdown(q['prompt'])}</div>{prompt_source}</section>{solution_section}<section id="how-to-run"><h2>How to run</h2>{how_to_run}</section></article>
<nav class="task-adjacent" aria-label="Adjacent tasks">{prev_link}<a href="{tasks_url(b)}">Task index</a>{next_link}</nav>'''
    relative = output_path(site_url(task_url(q)))
    write(relative+'index.html',layout(q['title'],body,description=q['title']))


def about():
    body = '''<h1>About Benchopedia</h1><article class="prose"><p>Benchopedia is a reference for AI benchmarks: what they measure, how they are scored, and the tasks they contain.</p>
<section id="contribute"><h2>Corrections and suggestions</h2><p>To report an error or suggest a benchmark, <a href="https://github.com/khooeee/benchopedia/issues">open an issue on GitHub</a>.</p></section></article>'''
    write('about/index.html',layout('About',body,'about'))
    write('404.html',layout('Page not found','<h1>Page not found</h1><p>This address does not match a benchmark or task.</p><p><a href="/">Return to the benchmark index</a></p>'))


def main():
    global BENCHMARKS, TASKS
    build_sqlite()
    with sqlite3.connect(ROOT/'build'/'benchopedia.db') as db:
        db.row_factory = sqlite3.Row
        BENCHMARKS = [dict(r) for r in db.execute('SELECT * FROM benchmark ORDER BY name')]
        TASKS = [dict(r) for r in db.execute('SELECT * FROM task ORDER BY benchmark_id, key')]
    tasks_by_benchmark = {b['id']:[] for b in BENCHMARKS}
    for b in BENCHMARKS:
        # Rendered once per benchmark; each task page fills in its own {{key}}.
        b['how_to_run_html'] = markdown(b['how_to_run'] or '')
    for q in TASKS:
        q['title'] = task_title(q['prompt'])
        tasks_by_benchmark[q['benchmark_id']].append(q)
    OUT.mkdir(exist_ok=True)
    # Only this generator's output directory is cleared.
    for child in OUT.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    shutil.copytree(ROOT/'assets',OUT/'assets')
    home()
    for b in BENCHMARKS:
        benchmark_page(b)
        if b['task_count']:
            library(b, tasks_by_benchmark[b['id']])
    for i,q in enumerate(TASKS):
        same = lambda other: other if other and other['benchmark_id']==q['benchmark_id'] else None
        task_page(q,same(TASKS[i-1] if i else None),same(TASKS[i+1] if i+1<len(TASKS) else None))
    about()
    print(f'Built {len(list(OUT.rglob("*.html"))):,} pages in dist/')


if __name__ == '__main__':
    main()
