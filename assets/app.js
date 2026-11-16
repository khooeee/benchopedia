/* Progressive enhancement: every article and task has a static HTML page. */
(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const escape = (value) => String(value).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  document.addEventListener('keydown', (event) => {
    if (event.key === '/' && !event.metaKey && !event.ctrlKey && !event.altKey && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) && !document.activeElement.isContentEditable) {
      event.preventDefault();
      ($('#task-search') || $('#benchmark-search'))?.focus();
    }
  });

  if ($('#benchmark-search')) {
    const search = $('#benchmark-search');
    const rows = [...document.querySelectorAll('[data-benchmark]')];
    const params = new URLSearchParams(location.search);
    search.value = params.get('q') || '';
    function filterBenchmarks() {
      const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
      let count = 0;
      rows.forEach((row) => {
        row.hidden = !terms.every((term) => row.dataset.search.includes(term));
        if (!row.hidden) count++;
      });
      document.querySelectorAll('.year-group').forEach((group) => {
        group.hidden = [...group.querySelectorAll('[data-benchmark]')].every((row) => row.hidden);
      });
      $('#benchmark-count').textContent = `${count} benchmark${count === 1 ? '' : 's'}`;
      $('#benchmark-empty').hidden = count !== 0;
      const params = new URLSearchParams();
      if (search.value) params.set('q', search.value);
      history.replaceState(null, '', '/' + (params.size ? '?' + params : ''));
    }
    search.addEventListener('input', filterBenchmarks);
    $('.search-form').addEventListener('submit', (event) => { event.preventDefault(); filterBenchmarks(); });
    $('#reset-benchmarks').addEventListener('click', () => {
      search.value = '';
      filterBenchmarks();
      search.focus();
    });
    filterBenchmarks();
  }

  if ($('#copy-prompt')) {
    $('#copy-prompt').addEventListener('click', async () => {
      const status = $('#copy-status');
      try {
        await navigator.clipboard.writeText(JSON.parse($('#prompt-data').textContent));
        $('#copy-prompt').textContent = 'copied';
        status.textContent = 'Original prompt copied to clipboard.';
        setTimeout(() => { $('#copy-prompt').textContent = 'copy prompt'; }, 2000);
      } catch {
        status.classList.remove('sr-only');
        status.textContent = 'Clipboard unavailable. Select the problem statement below and copy it manually.';
      }
    });
  }

  if (!$('#task-search')) return;
  const fields = {q:$('#task-search'),benchmark:$('#filter-benchmark')};
  let tasks = [], page = 1;
  const pageSize = 25;
  const initialParams = new URLSearchParams(location.search);
  for (const [key, field] of Object.entries(fields)) {
    const value = initialParams.get(key);
    if (value !== null && (field.tagName !== 'SELECT' || [...field.options].some((o) => o.value === value))) field.value = value;
  }
  page = Math.max(1, Number.parseInt(initialParams.get('page'), 10) || 1);

  function updateURL() {
    const params = new URLSearchParams();
    for (const [key, field] of Object.entries(fields)) {
      if (field.value) params.set(key, field.value);
    }
    if (page > 1) params.set('page', page);
    history.replaceState(null, '', '/tasks/' + (params.size ? '?' + params : ''));
  }

  function render() {
    const terms = fields.q.value.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
    const filtered = tasks.filter((q) => (
      (!fields.benchmark.value || q.benchmark_id === fields.benchmark.value) &&
      terms.every((term) => q.search.includes(term))
    ));
    const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
    page = Math.min(page, pages);
    const visible = filtered.slice((page-1)*pageSize, page*pageSize);
    const rows = visible.map((q) => {
      const url = escape(q.url);
      const source = q.source_url ? ` [<a href="${escape(q.source_url)}">source</a>]` : '';
      return `<li><div class="entry-links"><a href="${url}">${escape(q.key)}</a>${source}</div><div class="entry-title"><a href="${url}">${escape(q.title)}</a></div><div class="entry-meta">Benchmark: <a href="${escape(q.benchmark_url)}">${escape(q.benchmark_name)}</a></div></li>`;
    }).join('');
    $('#task-results').innerHTML = `<ol class="entry-list" start="${(page-1)*pageSize+1}">${rows}</ol>`;
    $('#task-results').hidden = !filtered.length;
    $('#task-empty').hidden = !!filtered.length;
    const first = (page-1)*pageSize+1, last = Math.min(page*pageSize,filtered.length);
    $('#task-count').textContent = filtered.length ? `${first}–${last} of ${filtered.length.toLocaleString()} tasks` : '0 tasks';
    $('#page-status').textContent = `Page ${page} of ${pages}`;
    $('#page-prev').disabled = page <= 1;
    $('#page-next').disabled = page >= pages;
    $('.pagination').hidden = !filtered.length;
    updateURL();
  }

  function reset() {
    for (const field of Object.values(fields)) field.value = '';
    page = 1;
    render();
  }
  function scrollToResults() {
    $('.library-summary').scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
  }
  let timer;
  fields.q.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => { page = 1; render(); }, 120);
  });
  for (const [key, field] of Object.entries(fields)) {
    if (key !== 'q') field.addEventListener('change', () => { page = 1; render(); });
  }
  $('#clear-filters').addEventListener('click', reset);
  $('[data-clear-tasks]').addEventListener('click', reset);
  $('#page-prev').addEventListener('click', () => { page--; render(); scrollToResults(); });
  $('#page-next').addEventListener('click', () => { page++; render(); scrollToResults(); });
  // Do not replace server-rendered tasks or react to controls until the index is ready.
  Object.values(fields).forEach((field) => { field.disabled = true; });
  $('#page-next').disabled = true;
  $('#clear-filters').disabled = true;
  fetch('/assets/tasks.json').then((response) => {
    if (!response.ok) throw new Error('Task index could not be loaded');
    return response.json();
  }).then((data) => {
    tasks = data.map((q) => ({...q, search: [q.title,q.key,q.prompt].join(' ').toLocaleLowerCase()}));
    Object.values(fields).forEach((field) => { field.disabled = false; });
    $('#clear-filters').disabled = false;
    render();
  }).catch(() => {
    $('#task-count').innerHTML = 'Search is unavailable. <a href="/tasks/all/">Browse all tasks instead →</a>';
    $('.pagination').hidden = true;
  });
})();
