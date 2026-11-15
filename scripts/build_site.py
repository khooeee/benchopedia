"""Generate the complete static encyclopedia from the validated SQLite database.

Run `python3 scripts/build_site.py`; no third-party packages are required.
"""

import collections
import html
import json
import re
import shutil
import sqlite3
from datetime import date
from pathlib import Path
from urllib.parse import quote, urlencode

from build import main as build_database

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dist"
DIFFICULTIES = ["<15 min fix", "15 min - 1 hour", "1-4 hours", ">4 hours"]
DIFFICULTY_LABELS = {
    "<15 min fix": "Under 15 min", "15 min - 1 hour": "15 min–1 hour",
    "1-4 hours": "1–4 hours", ">4 hours": "Over 4 hours",
}


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


def question_title(prompt):
    for line in re.sub(r"<!--.*?-->", "", prompt, flags=re.S).splitlines():
        line = line.strip().lstrip("# ")
        if line:
            return line.replace("`", "")[:220]
    return "Untitled task"


def question_url(q):
    return f'/benchmarks/{quote(q["benchmark_id"], safe="")}/questions/{quote(q["key"], safe="")}/'


def benchmark_url(b):
    return f'/benchmarks/{quote(b["id"], safe="")}/'


def write(path, content):
    target = OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")



def layout(title, body, active="benchmarks", description="Descriptions, datasets, and questions for AI benchmarks."):
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
<nav aria-label="Main navigation">{nav('benchmarks','/','Benchmarks')} <span aria-hidden="true">|</span> {nav('questions','/questions/','Questions')} <span aria-hidden="true">|</span> {nav('about','/about/','About')}</nav></div></header>
<main id="main" tabindex="-1">{body}</main>
<footer><a href="/about/">About Benchopedia</a> · <a href="https://github.com/khooeee/benchopedia/issues">Corrections &amp; suggestions</a></footer>
</body></html>'''


def task_list(rows, start=1):
    entries = []
    for q in rows:
        attrs = q['attrs']
        url = question_url(q)
        source = f' · <a href="{esc(q["source_url"])}">source</a>' if q.get('source_url') else ''
        entries.append(f'''<li><div class="entry-links"><a href="{url}">{esc(q['key'])}</a> [<a href="{url}">question</a>{source}]</div>
<div class="entry-title"><a href="{url}">{esc(q['title'])}</a></div>
<div class="entry-meta">Repository: {esc(attrs.get('repo','—'))} · Human fix time: {esc(DIFFICULTY_LABELS.get(attrs.get('difficulty'),'Not annotated'))}</div></li>''')
    return f'<ol class="entry-list" start="{start}">' + ''.join(entries) + '</ol>'


def home():
    categories = sorted({b.get('category','Other') for b in BENCHMARKS})
    options = ''.join(f'<option value="{esc(c)}">{esc(c)}</option>' for c in categories)
    ordered = sorted(BENCHMARKS, key=lambda b: (b['released_on'],b['name']), reverse=True)
    groups = []
    for year in sorted({b['released_on'][:4] for b in ordered}, reverse=True):
        entries = []
        for b in (b for b in ordered if b['released_on'].startswith(year)):
            url = benchmark_url(b)
            entries.append(f'''<li data-benchmark data-category="{esc(b.get('category','Other'))}" data-search="{esc((b['name']+' '+b['id']+' '+b['summary']+' '+b.get('category','')).lower())}">
<div class="entry-links"><a href="{url}">{esc(b['id'])}</a> [<a href="{url}">article</a> · <a href="/questions/?benchmark={quote(b['id'])}">questions</a> · <a href="{esc(b['homepage_url'])}">website</a> · <a href="{esc(b['dataset_url'])}">dataset</a>]</div>
<div class="entry-title"><a href="{url}">{esc(b['name'])}</a></div>
<p class="entry-summary">{esc(b['summary'])}</p>
<div class="entry-meta">Subject: {esc(b.get('category','Other'))}<br>Released: {esc(b['released_on'])} · Questions: {b['question_count']:,} · Metric: {esc(b.get('metric','Not documented'))}</div></li>''')
        groups.append(f'<section class="year-group"><h2>{year}</h2><ol class="entry-list">' + ''.join(entries) + '</ol></section>')
    body = f'''<h1>AI benchmarks</h1><p class="page-description">Descriptions, datasets, and the questions behind each benchmark.</p>
<form class="search-form" role="search"><label for="benchmark-search">Search:</label> <input type="search" id="benchmark-search" name="q" placeholder="Name, description, or subject"> <label for="benchmark-category">Subject:</label> <select id="benchmark-category" name="subject"><option value="">All subjects</option>{options}</select> <button type="submit">Search</button></form>
<p class="list-summary"><span id="benchmark-count" role="status" aria-live="polite">{len(BENCHMARKS)} benchmark{'s' if len(BENCHMARKS)!=1 else ''}</span> · Listed by release year, newest first</p>
<div id="catalog">{''.join(groups)}</div><div id="benchmark-empty" hidden><p>No benchmarks match your search.</p><button type="button" id="reset-benchmarks">Clear search</button></div>'''
    write('index.html',layout('AI benchmarks',body))


def distribution(counter, total, labels=None, b_id=None):
    rows = []
    for name,count in counter.items():
        label = esc((labels or {}).get(name,name))
        if b_id:
            label = f'<a href="/questions/?{esc(urlencode({"benchmark":b_id,"repo":name}))}">{label}</a>'
        rows.append(f'<tr><th scope="row">{label}</th><td>{count}</td><td>{count/total:.1%}</td></tr>')
    heading = 'Repository' if b_id else 'Human fix time'
    return f'<table class="data-table"><thead><tr><th scope="col">{heading}</th><th scope="col">Questions</th><th scope="col">Share</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table>'


def benchmark_page(b):
    qs = [q for q in QUESTIONS if q['benchmark_id']==b['id']]
    repos = collections.Counter(q['attrs'].get('repo','Unknown') for q in qs)
    difficulty = collections.Counter(q['attrs'].get('difficulty','Not annotated') for q in qs)
    facts = [('Subject',b.get('category','Not documented')),('Task',b.get('task','Not documented')),('Language',b.get('language','Not documented')),('Released',b['released_on']),('Questions',f'{len(qs):,}'),('Metric',b.get('metric','Not documented'))]
    sources = json.loads(b.get('sources','[]'))
    source_list = ''.join(f'<li><a href="{esc(s["url"])}">{esc(s["title"])}</a></li>' for s in sources)
    body = f'''<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Benchmarks</a> &gt; {esc(b['name'])}</nav>
<h1>{esc(b['name'])}</h1><p class="resource-links">[<a href="/questions/?benchmark={quote(b['id'])}">browse {len(qs):,} questions</a> · <a href="{esc(b['homepage_url'])}">official website</a> · <a href="{esc(b['dataset_url'])}">dataset</a>]</p>
<p>{esc(b['summary'])}</p><dl class="metadata">{''.join(f'<div><dt>{esc(k)}:</dt><dd>{esc(v)}</dd></div>' for k,v in facts)}</dl>
<nav class="contents" aria-label="Article sections">Contents: <a href="#overview">Overview</a> · <a href="#methodology">Methodology</a> · <a href="#scoring">Scoring</a> · <a href="#dataset">Dataset</a> · <a href="#limitations">Limitations</a> · <a href="#sources">Sources</a></nav>
<article class="prose"><section id="overview"><h2>Overview</h2>{markdown(b.get('overview',b['summary']))}</section>
<section id="methodology"><h2>Methodology</h2>{markdown(b.get('methodology','Not yet documented.'))}</section>
<section id="scoring"><h2>Scoring</h2>{markdown(b.get('scoring','Not yet documented.'))}</section>
<section id="dataset"><h2>Dataset</h2><p>{len(qs):,} questions from {len(repos)} repositories in this snapshot. <a href="/questions/?benchmark={quote(b['id'])}">Browse questions</a>.</p>
<h3>By repository</h3>{distribution(dict(repos.most_common()),len(qs),b_id=b['id'])}
<h3>Estimated human fix time</h3><p class="annotation">Upstream difficulty labels describe human fix time, not model completion time.</p>{distribution({k:difficulty[k] for k in DIFFICULTIES if difficulty[k]},len(qs),DIFFICULTY_LABELS)}</section>
<section id="limitations"><h2>Limitations</h2>{markdown(b.get('limitations','Not yet documented.'))}</section>
<section id="sources"><h2>Sources</h2><ol>{source_list}</ol><details class="snapshot"><summary>Dataset revision</summary><p>Snapshot of <a href="{esc(b['dataset_url'])}">the upstream dataset</a> at revision <code>{esc(b['dataset_revision'])}</code>.</p></details></section></article>'''
    write(f'benchmarks/{b["id"]}/index.html',layout(b['name'],body,description=b['summary']))


def library():
    repos = sorted({q['attrs']['repo'] for q in QUESTIONS if 'repo' in q['attrs']})
    option = lambda val,label: f'<option value="{esc(val)}">{esc(label)}</option>'
    selectors = f'''<label>Benchmark: <select id="filter-benchmark"><option value="">All benchmarks</option>{''.join(option(b['id'],b['name']) for b in BENCHMARKS)}</select></label>
<label>Repository: <select id="filter-repo"><option value="">All repositories</option>{''.join(option(r,r) for r in repos)}</select></label>
<label>Human fix time: <select id="filter-difficulty"><option value="">Any duration</option>{''.join(option(k,DIFFICULTY_LABELS[k]) for k in DIFFICULTIES)}</select></label>'''
    body = f'''<h1>Questions</h1><p class="page-description">Original tasks from the benchmark datasets.</p>
<section class="question-library" aria-label="Browse questions"><label class="question-search-label" for="question-search">Search:</label> <input type="search" id="question-search" placeholder="Question text, task ID, or repository">
<div class="filter-bar">{selectors}<button type="button" id="clear-filters">Clear filters</button></div>
<div class="library-summary"><p id="question-count" role="status" aria-live="polite">1–{min(25,len(QUESTIONS))} of {len(QUESTIONS):,} questions</p><label>Sort: <select id="question-sort"><option value="id">Task ID</option><option value="title">Title A–Z</option><option value="difficulty">Human fix time</option></select></label></div>
<nav class="pagination" aria-label="Question pages"><button type="button" id="page-prev" disabled>Previous</button> <span id="page-status">Page 1 of {max(1,(len(QUESTIONS)+24)//25)}</span> <button type="button" id="page-next">Next</button></nav>
<div id="question-results">{task_list(QUESTIONS[:25])}</div><div id="question-empty" hidden><p>No questions match your search.</p><button type="button" data-clear-questions>Clear filters</button></div>
<p class="all-questions-link"><a href="/questions/all/">View all {len(QUESTIONS):,} questions on one page</a></p><noscript><p>Search and filters require JavaScript. Use the complete question index above to browse without it.</p></noscript></section>'''
    write('questions/index.html',layout('Questions',body,'questions'))
    write('questions/all/index.html',layout('All questions','<h1>All questions</h1><p><a href="/questions/">Search and filter questions</a></p>'+task_list(QUESTIONS),'questions'))
    search_data = [{k:q[k] for k in ('benchmark_id','key','title','prompt','attrs','source_url')} | {'url':question_url(q)} for q in QUESTIONS]
    write('assets/questions.json',json.dumps(search_data,ensure_ascii=False,separators=(',',':')))


def question_page(q, previous, following):
    b = next(b for b in BENCHMARKS if b['id']==q['benchmark_id'])
    attrs = q['attrs']
    prev_link = f'<a href="{question_url(previous)}">Previous question</a>' if previous else '<span></span>'
    next_link = f'<a href="{question_url(following)}">Next question</a>' if following else '<span></span>'
    facts = [('Benchmark',f'<a href="{benchmark_url(b)}">{esc(b["name"])}</a>'),('Repository',f'<a href="/questions/?{esc(urlencode({"repo":attrs.get("repo","")}))}">{esc(attrs.get("repo","—"))}</a>'),('Human fix time',esc(DIFFICULTY_LABELS.get(attrs.get('difficulty'),'Not annotated'))),('Pull request created',esc(attrs.get('created_at','—')[:10])),('Installation version',esc(attrs.get('version','—')))]
    base_commit = attrs.get('base_commit','')
    if base_commit and attrs.get('repo'):
        facts.append(('Base commit',f'<a href="https://github.com/{esc(attrs["repo"])}/tree/{esc(base_commit)}"><code>{esc(base_commit)}</code></a>'))
    tests = ''.join(f'<li><code>{esc(t)}</code></li>' for t in attrs.get('fail_to_pass',[]))
    source_link = f'<a href="{esc(q["source_url"])}">source pull request</a> · ' if q.get('source_url') else ''
    body = f'''<nav class="breadcrumb" aria-label="Breadcrumb"><a href="/">Benchmarks</a> &gt; <a href="{benchmark_url(b)}">{esc(b['name'])}</a> &gt; <a href="/questions/?benchmark={quote(b['id'])}">Questions</a></nav>
<p class="task-id">{esc(q['key'])}</p><h1>{esc(q['title'])}</h1>
<p class="resource-links">[{source_link}<a href="prompt.txt" download>download prompt</a> · <button type="button" id="copy-prompt" class="link-button">copy prompt</button>]</p><p class="sr-only" role="status" id="copy-status"></p>
<dl class="metadata">{''.join(f'<div><dt>{esc(k)}:</dt><dd>{v}</dd></div>' for k,v in facts)}</dl>
<article class="prose"><section><h2>Problem statement</h2><div class="prompt-content">{markdown(q['prompt'])}</div></section>
<section><h2>Evaluation</h2><details><summary>{len(attrs.get('fail_to_pass',[]))} failing test(s) to resolve</summary><ul class="test-list">{tests}</ul></details><p class="annotation">The dataset also records {attrs.get('pass_to_pass_count',0):,} previously passing tests.</p></section></article>
<nav class="question-adjacent" aria-label="Adjacent questions">{prev_link}<a href="/questions/?benchmark={quote(b['id'])}">Question index</a>{next_link}</nav>
<script type="application/json" id="prompt-data">{json.dumps(q['prompt'],ensure_ascii=False).replace('<',chr(92)+'u003c')}</script>'''
    relative = question_url(q).lstrip('/')
    write(relative+'index.html',layout(q['title'],body,'questions',description=q['title']))
    write(relative+'prompt.txt',q['prompt'])


def about():
    body = '''<h1>About Benchopedia</h1><article class="prose"><p>Benchopedia is a reference for AI benchmarks: what they measure, how they are scored, and the questions they contain.</p>
<section id="sources"><h2>Sources and scope</h2><p>Articles cite original documentation and datasets. Questions preserve the imported prompts, and dataset counts are calculated from the imported snapshot.</p></section>
<section id="contribute"><h2>Corrections and suggestions</h2><p>To report an error or suggest a benchmark, <a href="https://github.com/khooeee/benchopedia/issues">open an issue on GitHub</a>.</p></section></article>'''
    write('about/index.html',layout('About',body,'about'))
    write('404.html',layout('Page not found','<h1>Page not found</h1><p>This address does not match a benchmark or question.</p><p><a href="/">Return to the benchmark index</a></p>'))


def main():
    global BENCHMARKS, QUESTIONS
    build_database()
    with sqlite3.connect(ROOT/'build'/'benchopedia.db') as db:
        db.row_factory = sqlite3.Row
        BENCHMARKS = [dict(r) for r in db.execute('SELECT b.*, a.category, a.task, a.metric, a.language, a.overview, a.methodology, a.scoring, a.limitations, a.sources FROM benchmark b LEFT JOIN benchmark_article a ON a.benchmark_id=b.id ORDER BY b.name')]
        # Missing editorial content must not prevent a new benchmark from appearing.
        BENCHMARKS = [{k:v for k,v in b.items() if v is not None} for b in BENCHMARKS]
        QUESTIONS = [dict(r) for r in db.execute('SELECT * FROM question ORDER BY benchmark_id, key')]
    for q in QUESTIONS:
        q['attrs'] = json.loads(q['attrs'])
        q['title'] = question_title(q['prompt'])
    OUT.mkdir(exist_ok=True)
    # Only this generator's output directory is cleared.
    for child in OUT.iterdir():
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
    shutil.copytree(ROOT/'web'/'assets',OUT/'assets')
    home()
    for b in BENCHMARKS:
        benchmark_page(b)
    library()
    for i,q in enumerate(QUESTIONS):
        same = lambda other: other if other and other['benchmark_id']==q['benchmark_id'] else None
        question_page(q,same(QUESTIONS[i-1] if i else None),same(QUESTIONS[i+1] if i+1<len(QUESTIONS) else None))
    about()
    print(f'Built {len(list(OUT.rglob("*.html"))):,} pages in dist/')


if __name__ == '__main__':
    main()
