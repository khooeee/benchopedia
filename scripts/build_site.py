"""Generate the complete static encyclopedia from the validated SQLite database.

Run `python3 scripts/build_site.py`; no third-party packages are required.
"""

import argparse
from collections import Counter
import html
import json
import re
import shutil
import sqlite3
from pathlib import Path
from contextlib import closing
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


def run_url(r):
    # Also a sibling of tasks/, so a run ID cannot collide with a task key.
    return f'/benchmarks/{quote(r["benchmark_id"], safe="")}/runs/{quote(r["id"], safe="")}/'


def run_task_url(r, key):
    return run_url(r) + f'tasks/{quote(key, safe="")}/'


REPOSITORY = 'https://github.com/khooeee/benchopedia'
STATUS_TEXT = {
    'solved': 'a run passed this task',
    'open': 'at least one completed evaluation failed and zero runs have passed',
    'untested': 'no run has tried this task yet',
    'pending': 'attempts exist and evaluation is incomplete',
}


def label(value):
    """A pass/fail result, attempt verdict or task status, spelled out for every reader."""
    return f'<span class="status status-{esc(value)}">{esc(value)}</span>'


def facts_list(facts):
    return '<dl class="metadata">' + ''.join(f'<div><dt>{esc(k)}:</dt><dd>{v}</dd></div>' for k, v in facts) + '</dl>'


def run_title(r):
    return f"{r['model']['name']} ({r['profile']})"


def runs_table(runs):
    rows = []
    for r in runs:
        passed = sum(t['result'] == 'pass' for t in r['tasks'])
        failed = sum(t['result'] == 'fail' for t in r['tasks'])
        pending = len(r['tasks']) - passed - failed
        if r['finished_at']:
            status = f"finished {esc(r['finished_at'][:10])}"
        elif r['stopped_at']:
            status = f"stopped {esc(r['stopped_at'][:10])}"
        else:
            status = 'in progress'
        rows.append(f'''<tr><td><a href="{run_url(r)}">{esc(r['id'])}</a></td><td>{esc(run_title(r))}</td>
<td class="number">{r['attempts_per_task']}</td><td class="number">{len(r['tasks']):,}</td><td class="number">{passed:,}</td>
<td class="number">{failed:,}</td><td class="number">{pending:,}</td><td>{status}</td></tr>''')
    return ('<div class="table-scroll"><table><thead><tr><th>Run</th><th>Model</th><th>Attempts per task</th><th>Tasks tried</th>'
            '<th>Passed</th><th>Failed</th><th>Pending</th><th>Status</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div>')


def results_section(b, runs, statuses):
    counts = {status: sum(s == status for s in statuses.values()) for status in STATUS_TEXT}
    links = ', '.join(f'<a href="{tasks_url(b)}?status={status}">{counts[status]:,} {status}</a>' for status in STATUS_TEXT)
    return f'''<p>A task passes a run when every required attempt is correct. An unparseable reply counts as a failed attempt. Completed failures stay open until a run passes the task. Open the run pages to see each grade and trajectory.</p>
<p>Of {b['task_count']:,} tasks: {links}.</p>{runs_table(runs)}'''


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
<nav aria-label="Main navigation">{nav('benchmarks','/','Benchmarks')} <span aria-hidden="true">|</span> {nav('open-tasks','/open-tasks/','Open tasks')} <span aria-hidden="true">|</span> {nav('about','/about/','About')}</nav></div></header>
<main id="main" tabindex="-1">{body}</main>
<footer><a href="/about/">About Benchopedia</a> · <a href="https://github.com/khooeee/benchopedia/issues">Corrections &amp; suggestions</a></footer>
</body></html>'''
    return re.sub(r'(href|src)="(/(?!/)[^"]*)"',
                  lambda match: f'{match[1]}="{site_url(match[2])}"', page)


def task_list(rows, start=1):
    entries = []
    for q in rows:
        url = task_url(q)
        status = ' ' + label(q['status']) if q.get('status') else ''
        entries.append(f'''<li><div class="entry-links"><a href="{url}">{esc(q['key'])}</a>{status}</div>
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


def benchmark_page(b, example=None, runs=(), statuses=None):
    # Excluded tasks link to the License section, which explains why.
    tasks = esc(task_count_label(b)) if b['task_count'] else '<a href="#license">not included</a>'
    facts = [('Released',esc(b['released_on'])),('Tasks',tasks)]
    task_link = f'<a href="{tasks_url(b)}">browse {b["task_count"]:,} tasks</a> · ' if b['task_count'] else ''
    sources = json.loads(b['sources'])
    source_list = ''.join(f'<li><a href="{esc(s["url"])}">{esc(s["title"])}</a></li>' for s in sources)
    # The review's own title would duplicate the section heading.
    license_text = re.sub(r"\A# [^\n]*\n", "", b['redistribution_review'])
    sections = [('overview','Overview',markdown(b['overview'])),
                ('methodology','Methodology',markdown(b['methodology'])),
                ('scoring','Scoring',markdown(b['scoring']))]
    if example:
        # The guide's code runs one task; an example task stands in for {{key}}.
        guide = markdown(b['how_to_run']).replace('{{key}}', esc(example['key']))
        sections.append(('how-to-run','How to run',f'''<p>These steps run and score task <a href="{task_url(example)}">{esc(example['key'])}</a>. Set <code>key</code> to another task's key to run that task instead.</p>{guide}'''))
    if runs:
        sections.append(('results','Results',results_section(b, runs, statuses)))
    sections += [('limitations','Limitations',markdown(b['limitations'])),
                 ('license','License',markdown(license_text)),
                 ('sources','Sources',f'''<ol>{source_list}</ol><details class="snapshot"><summary>Dataset revision</summary><p>Snapshot of <a href="{esc(b['dataset_url'])}">the upstream dataset</a> at revision <code>{esc(b['dataset_revision'])}</code>.</p></details>''')]
    contents = ''.join(f'<li><a href="#{key}">{title}</a></li>' for key,title,_ in sections)
    article = '\n'.join(f'<section id="{key}"><h2>{title}</h2>{html}</section>' for key,title,html in sections)
    body = f'''<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Benchmarks</a> &gt; {esc(b['name'])}</nav>
<h1>{esc(b['name'])}</h1><p class="resource-links">[{task_link}<a href="{esc(b['homepage_url'])}">official website</a> · <a href="{esc(b['dataset_url'])}">dataset</a>]</p>
<p>{esc(b['summary'])}</p><dl class="metadata">{''.join(f'<div><dt>{esc(k)}:</dt><dd>{v}</dd></div>' for k,v in facts)}</dl>
<nav class="toc" aria-labelledby="toc-heading"><h2 id="toc-heading">Contents</h2><ol>{contents}</ol></nav>
<article class="prose">{article}</article>'''
    write(f'benchmarks/{b["id"]}/index.html',layout(b['name'],body,description=b['summary']))


def library(b, rows):
    """One benchmark's searchable task list, its one-page fallback and search index."""
    crumbs = f'<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Benchmarks</a> &gt; <a href="{benchmark_url(b)}">{esc(b["name"])}</a> &gt; Tasks</nav>'
    # Only benchmarks with runs have task statuses to filter by.
    status_filter = ''
    if any(q.get('status') for q in rows):
        options = ''.join(f'<option value="{s}">{s.capitalize()}</option>' for s in STATUS_TEXT)
        status_filter = f' <label for="task-status">Status:</label> <select id="task-status"><option value="">All</option>{options}</select>'
    body = f'''{crumbs}<h1>{esc(b['name'])} tasks</h1>
<section class="task-library" aria-label="Browse tasks" data-benchmark-id="{esc(b['id'])}"><div class="search-form" role="search"><label for="task-search">Search:</label> <input type="search" id="task-search" placeholder="Task text or task ID">{status_filter}</div>
<div class="library-summary"><p id="task-count" role="status" aria-live="polite">1–{min(25,len(rows))} of {len(rows):,} tasks</p></div>
<nav class="pagination" aria-label="Task pages"><button type="button" id="page-prev" disabled>Previous</button> <span id="page-status">Page 1 of {max(1,(len(rows)+24)//25)}</span> <button type="button" id="page-next">Next</button></nav>
<div id="task-results">{task_list(rows[:25])}</div><div id="task-empty" hidden><p>No tasks match your search.</p><button type="button" data-clear-tasks>Clear search</button></div>
<p class="all-tasks-link"><a href="{all_tasks_url(b)}">View all {len(rows):,} tasks on one page</a></p><noscript><p>Search requires JavaScript. Use the complete task index above to browse without it.</p></noscript></section>'''
    write(output_path(site_url(tasks_url(b)))+'index.html',layout(f"{b['name']} tasks",body))
    all_body = f'{crumbs}<h1>All {esc(b["name"])} tasks</h1><p><a href="{tasks_url(b)}">Search tasks</a></p>'+task_list(rows)
    write(output_path(site_url(all_tasks_url(b)))+'index.html',layout(f"All {b['name']} tasks",all_body))
    search_data = [{k:q[k] for k in ('key','title','prompt','prompt_source_url')} | {'url':site_url(task_url(q))}
                   | ({'status':q['status']} if q.get('status') else {}) for q in rows]
    write(f'assets/tasks/{b["id"]}.json',json.dumps(search_data,ensure_ascii=False,separators=(',',':')))


def task_results_section(q, results):
    rows = []
    for r, t in results:
        attempts = ', '.join(f'<a href="{run_task_url(r, q["key"])}#attempt-{a["number"]}">{esc(a["verdict"])}</a>'
                             for a in t['attempts'])
        rows.append(f'''<tr><td><a href="{run_url(r)}">{esc(r['id'])}</a></td><td>{esc(run_title(r))}</td>
<td><a href="{run_task_url(r, q['key'])}">{label(t['result'])}</a></td><td>{attempts}</td></tr>''')
    table = ('<div class="table-scroll"><table><thead><tr><th>Run</th><th>Model</th><th>Result</th><th>Attempts</th></tr></thead><tbody>'
             + ''.join(rows) + '</tbody></table></div>') if rows else ''
    first_solve = ''
    if q['status'] == 'solved':
        revision = next(b['dataset_revision'] for b in BENCHMARKS if b['id'] == q['benchmark_id'])
        passes = [(r, t) for r, t in results
                  if t['result'] == 'pass' and r['dataset_revision'] in (None, revision)]
        if passes:
            r, t = min(passes, key=lambda pair: (
                pair[1]['graded_at'] or max(a['started_at'] for a in pair[1]['attempts']),
                pair[0]['id'],
            ))
            first_solve = f'<p>First recorded solve by <a href="{run_task_url(r, q["key"])}">{esc(run_title(r))}</a>.</p>'
    return f'''<section id="results"><h2>Results</h2><p>{label(q['status'])} {STATUS_TEXT[q['status']].capitalize()}.</p>{first_solve}{table}</section>'''


def task_page(q, previous, following, results=()):
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
    results_section = task_results_section(q, results) if q.get('status') else ''
    body = f'''<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Benchmarks</a> &gt; <a href="{benchmark_url(b)}">{esc(b['name'])}</a> &gt; <a href="{tasks_url(b)}">Tasks</a> &gt; <span class="task-id" aria-current="page">{esc(q['key'])}</span></nav>
<h1>{esc(q['title'])}</h1>
<article class="prose">{environment_section}<section id="task-prompt"><h2>Task Prompt</h2><div class="prompt-content">{markdown(q['prompt'])}</div>{prompt_source}</section>{solution_section}{results_section}</article>
<nav class="task-adjacent" aria-label="Adjacent tasks">{prev_link}<a href="{tasks_url(b)}">Task index</a>{next_link}</nav>'''
    relative = output_path(site_url(task_url(q)))
    write(relative+'index.html',layout(q['title'],body,description=q['title']))


def run_page(b, r, tasks_by_key):
    model = r['model']
    passed = sum(t['result'] == 'pass' for t in r['tasks'])
    failed = sum(t['result'] == 'fail' for t in r['tasks'])
    pending = len(r['tasks']) - passed - failed
    after = json.loads(r['after_runs'])
    selection = 'every task' if not after else 'tasks left open by ' + ', '.join(
        f'<a href="{run_url({"benchmark_id": b["id"], "id": earlier})}">{esc(earlier)}</a>' for earlier in after)
    if r['selected_tasks'] is not None:
        selection = f'{len(json.loads(r["selected_tasks"])):,} tasks selected by key'
    elif r['local']:
        selection = 'local scratch selection'
    if r['finished_at']:
        progress, ended = '', [('Finished', esc(r['finished_at']))]
    elif r['stopped_at']:
        progress = ' before the run was stopped'
        ended = [('Stopped', esc(r['stopped_at'])),
                 ('Why it stopped', f'<span data-text="stop-reason">{esc(r["stop_reason"])}</span>')]
    else:
        progress, ended = ' so far; the run is still in progress', [('Finished', 'in progress')]
    facts = [('Model', f'<a href="{esc(model["homepage_url"])}">{esc(model["name"])}</a>'),
             ('Served as', f'<code>{esc(model["provider_model"])}</code> on {esc(model["provider"])}'),
             *([('Weights digest', f'<code>{esc(model["weights_digest"])}</code>')] if model["weights_digest"] else []),
             ('Profile', esc(r['profile'])),
             ('Attempts per task', str(r['attempts_per_task'])),
             ('Tasks selected', selection),
             ('Results', f'{passed:,} passed, {failed:,} failed, {pending:,} pending{progress}'),
             ('Started', esc(r['started_at'])),
             *ended,
             ('Commit', f'<a href="{REPOSITORY}/commit/{esc(r["commit_sha"])}"><code>{esc(r["commit_sha"])}</code></a>')]
    steps = ''.join(f'<li><p>{esc(c["purpose"])}</p><pre><code data-text="command-{c["number"]}">{esc(c["command"])}</code></pre></li>'
                    for c in r['commands'])
    environment = facts_list([(k.replace('_', ' ').capitalize(), f'<code>{esc(v)}</code>')
                              for k, v in json.loads(r['environment']).items()])
    # The benchmark's own grader is what most readers come to check, so it starts open.
    files = ''.join(f'''<details{' open' if f['path'].endswith('/eval.py') else ''}><summary><code>{esc(f['path'])}</code></summary>
<pre><code data-text="file:{esc(f['path'])}">{esc(f['content'])}</code></pre></details>''' for f in r['files'])
    stopped_steps = (' The run was stopped before the runner reached every task, so the runner command will try more tasks than this run did.'
                     if r['stopped_at'] else '')
    entries = []
    for t in r['tasks']:
        verdicts = ', '.join(esc(a['verdict']) for a in t['attempts'])
        url = run_task_url(r, t['task_key'])
        entries.append(f'''<li data-result="{esc(t['result'])}"><div class="entry-links"><a href="{url}">{esc(t['task_key'])}</a> {label(t['result'])} <span class="verdicts">attempts: {verdicts}</span></div>
<div class="entry-title"><a href="{url}">{esc(tasks_by_key[t['task_key']]['title'])}</a></div></li>''')
    sections = [('steps', 'Steps', f'<p>These commands produced this run. Run them in order to reproduce it.{stopped_steps}</p><ol class="steps">{steps}</ol>'),
                ('settings', 'Settings', f'<p>The options sent with every request, from the model\'s <code>{esc(r["profile"])}</code> profile.</p><pre><code>{esc(json.dumps(json.loads(r["settings"]), indent=2))}</code></pre>'),
                ('environment', 'Environment', environment),
                ('code', 'Code', f'<p>The files the runner read, copied when the run started.</p>{files}'),
                ('tasks', 'Tasks', f'''<form class="search-form"><label for="result-filter">Result:</label> <select id="result-filter"><option value="">All</option><option value="pass">Pass</option><option value="fail">Fail</option><option value="pending">Pending</option></select>
<span id="result-count" role="status" aria-live="polite">{len(r['tasks']):,} tasks</span></form><ol class="entry-list">{''.join(entries)}</ol>''')]
    contents = ''.join(f'<li><a href="#{key}">{title}</a></li>' for key, title, _ in sections)
    article = '\n'.join(f'<section id="{key}"><h2>{title}</h2>{html}</section>' for key, title, html in sections)
    body = f'''<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Benchmarks</a> &gt; <a href="{benchmark_url(b)}">{esc(b['name'])}</a> &gt; <a href="{benchmark_url(b)}#results">Results</a></nav>
<p class="task-id">Run</p><h1>{esc(r['id'])}</h1><p>{esc(run_title(r))} on {esc(b['name'])}.</p>{facts_list(facts)}
<nav class="toc" aria-labelledby="toc-heading"><h2 id="toc-heading">Contents</h2><ol>{contents}</ol></nav>
<article class="prose">{article}</article>'''
    write(output_path(site_url(run_url(r))) + 'index.html', layout(f"{r['id']} · {b['name']}", body, description=f"{run_title(r)} on {b['name']}"))


def model_call_view(attempt_number, call):
    request, response = json.loads(call['request']), json.loads(call['response'])
    sent = ''.join(f'''<div class="message"><p class="role">Sent: {esc(m.get('role', ''))} message</p><pre>{esc(m.get('content', ''))}</pre></div>'''
                   for m in request.get('messages', []))
    choices = response.get('choices') or [{}]
    reply = response.get('message') or choices[0].get('message', {})
    thinking = reply.get('thinking') or reply.get('reasoning')
    reasoning = ''
    if thinking:
        reasoning = f'''<details class="message"><summary>Reasoning ({len(thinking):,} characters)</summary><pre>{esc(thinking)}</pre></details>'''
    answer = f'''<div class="message"><p class="role">Received: {esc(reply.get('role', ''))} message</p><pre>{esc(reply.get('content', ''))}</pre></div>'''
    tokens = response.get('usage') or {}
    usage = facts_list([(k, esc(v)) for k, v in (('Latency', f"{call['latency_ms'] / 1000:,.1f} s"),
                                                 ('Input tokens', response.get('prompt_eval_count', tokens.get('prompt_tokens'))),
                                                 ('Output tokens', response.get('eval_count', tokens.get('completion_tokens'))),
                                                 ('Stop reason', response.get('done_reason', choices[0].get('finish_reason')))) if v is not None])
    raw = f'''<details><summary>Exact request and response JSON</summary><h4>Request</h4><pre class="wrap"><code>{esc(json.dumps(request, indent=2, ensure_ascii=False))}</code></pre>
<h4>Response</h4><pre class="wrap"><code>{esc(json.dumps(response, indent=2, ensure_ascii=False))}</code></pre></details>'''
    return f'<div class="model-call" id="attempt-{attempt_number}-call-{call["number"]}">{sent}{reasoning}{answer}{usage}{raw}</div>'


def run_task_page(b, r, t, q, previous, following):
    passed = sum(a['verdict'] == 'pass' for a in t['attempts'])
    attempts = []
    for a in t['attempts']:
        answer = f'<code>{esc(a["answer"])}</code>' if a['answer'] is not None else 'none found'
        calls = ''.join(model_call_view(a['number'], c) for c in a['calls'])
        attempts.append(f'''<section id="attempt-{a['number']}"><h2>Attempt {a['number']}: {label(a['verdict'])}</h2>
{facts_list([('Extracted answer', answer), ('Started', esc(a['started_at']))])}
<details><summary>Graded output</summary><pre class="wrap"><code data-text="output-{a['number']}">{esc(a['output'])}</code></pre></details>
<h3>Trajectory</h3>{calls}</section>''')
    solution = ''
    if q.get('solution') is not None:
        solution = f'<details><summary>Reference solution</summary><pre class="wrap"><code>{esc(q["solution"])}</code></pre></details>'
    prev_link = f'<a href="{run_task_url(r, previous)}">Previous task</a>' if previous else '<span></span>'
    next_link = f'<a href="{run_task_url(r, following)}">Next task</a>' if following else '<span></span>'
    body = f'''<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Benchmarks</a> &gt; <a href="{benchmark_url(b)}">{esc(b['name'])}</a> &gt; <a href="{benchmark_url(b)}#results">Results</a> &gt; <a href="{run_url(r)}">{esc(r['id'])}</a></nav>
<p class="task-id">{esc(q['key'])}</p><h1>{esc(q['title'])}</h1>
<p class="run-result" data-result="{esc(t['result'])}">Result: {label(t['result'])}: {passed} of {len(t['attempts'])} attempts passed.</p>
{facts_list([('Run', f'<a href="{run_url(r)}">{esc(r["id"])}</a>'), ('Model', esc(run_title(r))), ('Task', f'<a href="{task_url(q)}">{esc(q["key"])}</a>')])}
<article class="prose">{solution}{''.join(attempts)}</article>
<nav class="task-adjacent" aria-label="Adjacent tasks">{prev_link}<a href="{run_url(r)}#tasks">Run's tasks</a>{next_link}</nav>'''
    write(output_path(site_url(run_task_url(r, q['key']))) + 'index.html',
          layout(f"{q['key']} · {r['id']}", body, description=f"{run_title(r)} on {q['key']}"))


def about():
    body = '''<h1>About Benchopedia</h1><article class="prose"><p>Benchopedia is a reference for AI benchmarks: what they measure, how they are scored, and the tasks they contain.</p>
<section id="contribute"><h2>Corrections and suggestions</h2><p>To report an error or suggest a benchmark, <a href="https://github.com/khooeee/benchopedia/issues">open an issue on GitHub</a>.</p></section></article>'''
    write('about/index.html',layout('About',body,'about'))
    write('404.html',layout('Page not found','<h1>Page not found</h1><p>This address does not match a benchmark or task.</p><p><a href="/">Return to the benchmark index</a></p>'))


def open_tasks(statuses, results_by_task):
    counts = Counter(statuses.values())
    benchmarks = {b['id']: b for b in BENCHMARKS}
    rows = []
    options = {}
    for task in TASKS:
        key = task['benchmark_id'], task['key']
        if statuses[key] != 'open':
            continue
        b = benchmarks[key[0]]
        options[b['id']] = b['name']
        attempts = ' · '.join(f'<a href="{run_task_url(run, key[1])}">{esc(run["id"])}</a>'
                              for run, _ in results_by_task.get(key, ())
                              if run['dataset_revision'] in (None, b['dataset_revision']))
        rows.append(f'''<tr data-open-benchmark="{esc(b['id'])}"><td><a href="{benchmark_url(b)}">{esc(b['name'])}</a></td>
<td><a href="{task_url(task)}">{esc(task['title'])}</a> <span class="task-id">{esc(key[1])}</span></td><td>{attempts}</td></tr>''')
    evaluated = counts['open'] + counts['solved']
    body = f'''<h1>Open tasks</h1>
<p>Tasks with a completed failed evaluation and zero verified solves in Benchopedia's records. An evaluation passes when every required attempt is correct.</p>
{facts_list([('Evaluated', f"{evaluated:,} of {len(statuses):,}"), ('Open', f"{counts['open']:,}"),
             ('Solved', f"{counts['solved']:,}")])}'''
    if rows:
        choices = ''.join(f'<option value="{esc(key)}">{esc(name)}</option>'
                          for key, name in sorted(options.items(), key=lambda pair: pair[1].casefold()))
        body += f'''<div id="open-filter" class="search-form" hidden><label for="open-benchmark">Benchmark</label>
<select id="open-benchmark"><option value="">All</option>{choices}</select>
<span id="open-count" role="status">{len(rows):,} tasks</span></div>
<div class="table-scroll"><table><thead><tr><th>Benchmark</th><th>Task</th><th>Recorded attempts</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table></div>'''
    else:
        body += '<p>No tasks are open in the recorded results.</p>'
    write('open-tasks/index.html', layout('Open tasks', body, 'open-tasks'))


def load_runs(db):
    """Every run with its model, commands, code, and each task's attempts and model calls."""
    models = {m['id']: dict(m) for m in db.execute('SELECT * FROM model')}
    runs = [dict(r) | {'model': models[r['model_id']], 'commands': [], 'files': [], 'tasks': []}
            for r in db.execute('SELECT * FROM run ORDER BY benchmark_id, started_at, id')]
    by_id = {(r['benchmark_id'], r['id']): r for r in runs}
    for c in db.execute('SELECT * FROM run_command ORDER BY number'):
        by_id[(c['benchmark_id'], c['run_id'])]['commands'].append(dict(c))
    for f in db.execute('SELECT * FROM run_file ORDER BY path'):
        by_id[(f['benchmark_id'], f['run_id'])]['files'].append(dict(f))
    tasks = {}
    for t in db.execute('SELECT * FROM run_task ORDER BY task_key'):
        tasks[(t['benchmark_id'], t['run_id'], t['task_key'])] = dict(t) | {'attempts': []}
        by_id[(t['benchmark_id'], t['run_id'])]['tasks'].append(tasks[(t['benchmark_id'], t['run_id'], t['task_key'])])
    attempts = {}
    for a in db.execute('SELECT * FROM attempt ORDER BY number'):
        attempt = dict(a) | {'calls': []}
        attempts[(a['benchmark_id'], a['run_id'], a['task_key'], a['number'])] = attempt
        tasks[(a['benchmark_id'], a['run_id'], a['task_key'])]['attempts'].append(attempt)
    for c in db.execute('SELECT * FROM model_call ORDER BY number'):
        attempts[(c['benchmark_id'], c['run_id'], c['task_key'], c['attempt_number'])]['calls'].append(dict(c))
    return runs


def main(argv=None):
    global BENCHMARKS, TASKS, OUT
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local-runs', action='store_true', help='include qualifying local runs in build/local-site')
    args = parser.parse_args(argv)
    path = ROOT / 'build' / ('benchopedia-local.db' if args.local_runs else 'benchopedia.db')
    OUT = ROOT / ('build/local-site' if args.local_runs else 'dist')
    build_sqlite(args.local_runs, path)
    with closing(sqlite3.connect(path)) as db:
        db.row_factory = sqlite3.Row
        BENCHMARKS = [dict(r) for r in db.execute('SELECT * FROM benchmark ORDER BY name')]
        TASKS = [dict(r) for r in db.execute('SELECT * FROM task ORDER BY benchmark_id, key')]
        runs = load_runs(db)
        statuses = {(r['benchmark_id'], r['task_key']): r['status'] for r in db.execute('SELECT * FROM task_status')}
    tasks_by_benchmark = {b['id']:[] for b in BENCHMARKS}
    runs_by_benchmark = {b['id']:[] for b in BENCHMARKS}
    results_by_task = {}
    for r in runs:
        runs_by_benchmark[r['benchmark_id']].append(r)
        for t in r['tasks']:
            results_by_task.setdefault((r['benchmark_id'], t['task_key']), []).append((r, t))
    for q in TASKS:
        q['title'] = task_title(q['prompt'])
        # Statuses only mean something once a benchmark has runs.
        if runs_by_benchmark[q['benchmark_id']]:
            q['status'] = statuses[(q['benchmark_id'], q['key'])]
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
    open_tasks(statuses, results_by_task)
    for b in BENCHMARKS:
        rows = tasks_by_benchmark[b['id']]
        benchmark_runs = runs_by_benchmark[b['id']]
        benchmark_page(b, rows[0] if rows else None, benchmark_runs, {q['key']: q.get('status') for q in rows})
        if b['task_count']:
            library(b, rows)
        tasks_by_key = {q['key']: q for q in rows}
        for r in benchmark_runs:
            run_page(b, r, tasks_by_key)
            keys = [t['task_key'] for t in r['tasks']]
            for i, t in enumerate(r['tasks']):
                run_task_page(b, r, t, tasks_by_key[t['task_key']],
                              keys[i-1] if i else None, keys[i+1] if i+1 < len(keys) else None)
    for i,q in enumerate(TASKS):
        same = lambda other: other if other and other['benchmark_id']==q['benchmark_id'] else None
        task_page(q,same(TASKS[i-1] if i else None),same(TASKS[i+1] if i+1<len(TASKS) else None),
                  results_by_task.get((q['benchmark_id'], q['key']), ()))
    about()
    print(f'Built {len(list(OUT.rglob("*.html"))):,} pages in {OUT.relative_to(ROOT)}/')


if __name__ == '__main__':
    main()
