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


def write(path, content):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")



def layout(title, body, active="benchmarks", description="Descriptions, datasets, and tasks for AI benchmarks."):
    def nav(key, url, label):
        current = ' aria-current="page"' if active == key else ''
        return f'<a href="{url}"{current}>{label}</a>'

    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · Benchopedia</title><meta name="description" content="{esc(description)}">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="stylesheet" href="/assets/style.css"><script src="/assets/app.js" defer></script></head>
<body><a class="skip" href="#main">Skip to content</a>
<header class="site-header"><div class="header-inner"><a class="site-name" href="/">Benchopedia</a><span class="site-description">The AI benchmark encyclopedia</span>
<nav aria-label="Main navigation">{nav('benchmarks','/','Benchmarks')} <span aria-hidden="true">|</span> {nav('tasks','/tasks/','Tasks')} <span aria-hidden="true">|</span> {nav('about','/about/','About')}</nav></div></header>
<main id="main" tabindex="-1">{body}</main>
<footer><a href="/about/">About Benchopedia</a> · <a href="https://github.com/khooeee/benchopedia/issues">Corrections &amp; suggestions</a></footer>
</body></html>'''


def task_list(rows, start=1):
    entries = []
    for q in rows:
        url = task_url(q)
        source = f' [<a href="{esc(q["source_url"])}">source</a>]' if q.get('source_url') else ''
        entries.append(f'''<li><div class="entry-links"><a href="{url}">{esc(q['key'])}</a>{source}</div>
<div class="entry-title"><a href="{url}">{esc(q['title'])}</a></div>
<div class="entry-meta">Benchmark: <a href="{esc(q['benchmark_url'])}">{esc(q['benchmark_name'])}</a></div></li>''')
    return f'<ol class="entry-list" start="{start}">' + ''.join(entries) + '</ol>'


def home():
    ordered = sorted(BENCHMARKS, key=lambda b: (b['released_on'],b['name']), reverse=True)
    groups = []
    for year in sorted({b['released_on'][:4] for b in ordered}, reverse=True):
        entries = []
        for b in (b for b in ordered if b['released_on'].startswith(year)):
            url = benchmark_url(b)
            entries.append(f'''<li data-benchmark data-search="{esc((b['name']+' '+b['id']+' '+b['summary']).lower())}">
<div class="entry-title"><a href="{url}">{esc(b['name'])}</a></div>
<div class="entry-links"><a href="/tasks/?benchmark={quote(b['id'])}">tasks</a> · <a href="{esc(b['homepage_url'])}">website</a> · <a href="{esc(b['dataset_url'])}">dataset</a></div>
<p class="entry-summary">{esc(b['summary'])}</p>
<div class="entry-meta">Released: {esc(b['released_on'])} · Tasks: {b['task_count']:,}</div></li>''')
        groups.append(f'<section class="year-group"><h2>{year}</h2><ol class="entry-list">' + ''.join(entries) + '</ol></section>')
    body = f'''<h1>Benchmarks</h1>
<form class="search-form" role="search"><label for="benchmark-search">Search:</label> <input type="search" id="benchmark-search" name="q" placeholder="Name or description"> <button type="submit">Search</button></form>
<p class="list-summary"><span id="benchmark-count" role="status" aria-live="polite">{len(BENCHMARKS)} benchmark{'s' if len(BENCHMARKS)!=1 else ''}</span></p>
<div id="catalog">{''.join(groups)}</div><div id="benchmark-empty" hidden><p>No benchmarks match your search.</p><button type="button" id="reset-benchmarks">Clear search</button></div>'''
    write('index.html',layout('Benchmarks',body))


def benchmark_page(b):
    qs = [q for q in TASKS if q['benchmark_id']==b['id']]
    facts = [('Released',b['released_on']),('Tasks',f'{len(qs):,}')]
    sources = json.loads(b['sources'])
    source_list = ''.join(f'<li><a href="{esc(s["url"])}">{esc(s["title"])}</a></li>' for s in sources)
    body = f'''<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Benchmarks</a> &gt; {esc(b['name'])}</nav>
<h1>{esc(b['name'])}</h1><p class="resource-links">[<a href="/tasks/?benchmark={quote(b['id'])}">browse {len(qs):,} tasks</a> · <a href="{esc(b['homepage_url'])}">official website</a> · <a href="{esc(b['dataset_url'])}">dataset</a>]</p>
<p>{esc(b['summary'])}</p><dl class="metadata">{''.join(f'<div><dt>{esc(k)}:</dt><dd>{esc(v)}</dd></div>' for k,v in facts)}</dl>
<article class="prose"><section id="overview"><h2>Overview</h2>{markdown(b['overview'])}</section>
<section id="methodology"><h2>Methodology</h2>{markdown(b['methodology'])}</section>
<section id="scoring"><h2>Scoring</h2>{markdown(b['scoring'])}</section>
<section id="dataset"><h2>Dataset</h2><p>{len(qs):,} tasks in this snapshot. <a href="/tasks/?benchmark={quote(b['id'])}">Browse tasks</a> or visit <a href="{esc(b['dataset_url'])}">the upstream dataset</a>.</p></section>
<section id="limitations"><h2>Limitations</h2>{markdown(b['limitations'])}</section>
<section id="sources"><h2>Sources</h2><ol>{source_list}</ol><details class="snapshot"><summary>Dataset revision</summary><p>Snapshot of <a href="{esc(b['dataset_url'])}">the upstream dataset</a> at revision <code>{esc(b['dataset_revision'])}</code>.</p></details></section></article>'''
    write(f'benchmarks/{b["id"]}/index.html',layout(b['name'],body,description=b['summary']))


def library():
    option = lambda val,label: f'<option value="{esc(val)}">{esc(label)}</option>'
    selectors = f'<label>Benchmark: <select id="filter-benchmark"><option value="">All benchmarks</option>{"".join(option(b["id"],b["name"]) for b in BENCHMARKS)}</select></label>'
    body = f'''<h1>Tasks</h1><p class="page-description">Original tasks from the benchmark datasets.</p>
<section class="task-library" aria-label="Browse tasks"><label class="task-search-label" for="task-search">Search:</label> <input type="search" id="task-search" placeholder="Task text or task ID">
<div class="filter-bar">{selectors}<button type="button" id="clear-filters">Clear filters</button></div>
<div class="library-summary"><p id="task-count" role="status" aria-live="polite">1–{min(25,len(TASKS))} of {len(TASKS):,} tasks</p></div>
<nav class="pagination" aria-label="Task pages"><button type="button" id="page-prev" disabled>Previous</button> <span id="page-status">Page 1 of {max(1,(len(TASKS)+24)//25)}</span> <button type="button" id="page-next">Next</button></nav>
<div id="task-results">{task_list(TASKS[:25])}</div><div id="task-empty" hidden><p>No tasks match your search.</p><button type="button" data-clear-tasks>Clear filters</button></div>
<p class="all-tasks-link"><a href="/tasks/all/">View all {len(TASKS):,} tasks on one page</a></p><noscript><p>Search and filters require JavaScript. Use the complete task index above to browse without it.</p></noscript></section>'''
    write('tasks/index.html',layout('Tasks',body,'tasks'))
    write('tasks/all/index.html',layout('All tasks','<h1>All tasks</h1><p><a href="/tasks/">Search and filter tasks</a></p>'+task_list(TASKS),'tasks'))
    search_data = [{k:q[k] for k in ('benchmark_id','benchmark_name','benchmark_url','key','title','prompt','source_url')} | {'url':task_url(q)} for q in TASKS]
    write('assets/tasks.json',json.dumps(search_data,ensure_ascii=False,separators=(',',':')))


def task_page(q, previous, following):
    b = next(b for b in BENCHMARKS if b['id']==q['benchmark_id'])
    prev_link = f'<a href="{task_url(previous)}">Previous task</a>' if previous else '<span></span>'
    next_link = f'<a href="{task_url(following)}">Next task</a>' if following else '<span></span>'
    source_link = f'<a href="{esc(q["source_url"])}">source</a> · ' if q.get('source_url') else ''
    body = f'''<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Benchmarks</a> &gt; <a href="{benchmark_url(b)}">{esc(b['name'])}</a> &gt; <a href="/tasks/?benchmark={quote(b['id'])}">Tasks</a></nav>
<p class="task-id">{esc(q['key'])}</p><h1>{esc(q['title'])}</h1>
<p class="resource-links">[{source_link}<button type="button" id="copy-prompt" class="link-button">copy prompt</button>]</p><p class="sr-only" role="status" id="copy-status"></p>
<article class="prose"><section><h2>Task Prompt</h2><div class="prompt-content">{markdown(q['prompt'])}</div></section></article>
<nav class="task-adjacent" aria-label="Adjacent tasks">{prev_link}<a href="/tasks/?benchmark={quote(b['id'])}">Task index</a>{next_link}</nav>
<script type="application/json" id="prompt-data">{json.dumps(q['prompt'],ensure_ascii=False).replace('<',chr(92)+'u003c')}</script>'''
    relative = task_url(q).lstrip('/')
    write(relative+'index.html',layout(q['title'],body,'tasks',description=q['title']))


def about():
    body = '''<h1>About Benchopedia</h1><article class="prose"><p>Benchopedia is a reference for AI benchmarks: what they measure, how they are scored, and the tasks they contain.</p>
<section id="sources"><h2>Sources and scope</h2><p>Articles cite original documentation and datasets. Tasks preserve the imported prompts, and dataset counts are calculated from the imported snapshot.</p></section>
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
    benchmark_by_id = {b['id']:b for b in BENCHMARKS}
    for q in TASKS:
        q['title'] = task_title(q['prompt'])
        benchmark = benchmark_by_id[q['benchmark_id']]
        q['benchmark_name'] = benchmark['name']
        q['benchmark_url'] = benchmark_url(benchmark)
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
    library()
    for i,q in enumerate(TASKS):
        same = lambda other: other if other and other['benchmark_id']==q['benchmark_id'] else None
        task_page(q,same(TASKS[i-1] if i else None),same(TASKS[i+1] if i+1<len(TASKS) else None))
    about()
    print(f'Built {len(list(OUT.rglob("*.html"))):,} pages in dist/')


if __name__ == '__main__':
    main()
