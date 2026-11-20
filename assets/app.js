/* Progressive enhancement: every article and task has a static HTML page. */
(() => {
  'use strict';
  const $ = (selector) => document.querySelector(selector);
  const basePath = $('meta[name="site-base-path"]')?.content || '';
  const siteURL = (path) => basePath + path;
  const escape = (value) => String(value).replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  document.addEventListener('keydown', (event) => {
    if (event.key === '/' && !event.metaKey && !event.ctrlKey && !event.altKey && !/INPUT|TEXTAREA|SELECT/.test(document.activeElement.tagName) && !document.activeElement.isContentEditable) {
      event.preventDefault();
      ($('#task-search') || $('#benchmark-search'))?.focus();
    }
  });

  if ($('#benchmark-search')) {
    const search = $('#benchmark-search');
    const solutions = $('#filter-solutions');
    const tasks = $('#filter-tasks');
    const rows = [...document.querySelectorAll('[data-benchmark]')];
    const params = new URLSearchParams(location.search);
    search.value = params.get('q') || '';
    solutions.checked = params.get('has_solutions') === '1';
    tasks.checked = params.get('has_tasks') === '1';
    function filterBenchmarks() {
      const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
      let count = 0;
      rows.forEach((row) => {
        row.hidden = (tasks.checked && row.dataset.hasTasks !== 'true') ||
          (solutions.checked && row.dataset.hasSolutions !== 'true') ||
          !terms.every((term) => row.dataset.search.includes(term));
        if (!row.hidden) count++;
      });
      document.querySelectorAll('.year-group').forEach((group) => {
        group.hidden = [...group.querySelectorAll('[data-benchmark]')].every((row) => row.hidden);
      });
      $('#benchmark-count').textContent = `${count} benchmark${count === 1 ? '' : 's'}`;
      $('#benchmark-empty').hidden = count !== 0;
      const params = new URLSearchParams();
      if (search.value) params.set('q', search.value);
      if (solutions.checked) params.set('has_solutions', '1');
      if (tasks.checked) params.set('has_tasks', '1');
      history.replaceState(null, '', siteURL('/') + (params.size ? '?' + params : ''));
    }
    search.addEventListener('input', filterBenchmarks);
    solutions.addEventListener('change', filterBenchmarks);
    tasks.addEventListener('change', filterBenchmarks);
    $('.search-form').addEventListener('submit', (event) => { event.preventDefault(); filterBenchmarks(); });
    $('#reset-benchmarks').addEventListener('click', () => {
      search.value = '';
      solutions.checked = false;
      tasks.checked = false;
      filterBenchmarks();
      search.focus();
    });
    filterBenchmarks();
  }

  const openBenchmark = $('#open-benchmark');
  if (openBenchmark) {
    const rows = [...document.querySelectorAll('[data-open-benchmark]')];
    $('#open-filter').hidden = false;
    openBenchmark.addEventListener('change', () => {
      let count = 0;
      for (const row of rows) {
        row.hidden = !!openBenchmark.value && row.dataset.openBenchmark !== openBenchmark.value;
        if (!row.hidden) count++;
      }
      $('#open-count').textContent = `${count.toLocaleString()} task${count === 1 ? '' : 's'}`;
    });
  }

  // A run's page lists every task it tried.
  if ($('#result-filter')) {
    const filter = $('#result-filter');
    const items = [...document.querySelectorAll('[data-result]')];
    const requested = new URLSearchParams(location.search).get('result');
    filter.value = ['pass', 'fail', 'pending', 'scored'].includes(requested) ? requested : '';
    function filterResults() {
      let count = 0;
      items.forEach((item) => {
        item.hidden = !!filter.value && item.dataset.result !== filter.value;
        if (!item.hidden) count++;
      });
      $('#result-count').textContent = `${count.toLocaleString()} task${count === 1 ? '' : 's'}`;
      history.replaceState(null, '', location.pathname + (filter.value ? `?result=${filter.value}` : '') + location.hash);
    }
    filter.addEventListener('change', filterResults);
    filterResults();
  }

  const search = $('#task-search');
  if (!search) return;
  // Only benchmarks with runs offer a status filter.
  const status = $('#task-status');
  // Each benchmark has its own task page and search index.
  const benchmark = encodeURIComponent($('.task-library').dataset.benchmarkId);
  let tasks = [], page = 1;
  const pageSize = 25;
  const initialParams = new URLSearchParams(location.search);
  search.value = initialParams.get('q') || '';
  page = Math.max(1, Number.parseInt(initialParams.get('page'), 10) || 1);
  if (status) status.value = ['solved', 'open', 'untested', 'pending', 'scored'].includes(initialParams.get('status')) ? initialParams.get('status') : '';

  function updateURL() {
    const params = new URLSearchParams();
    if (search.value) params.set('q', search.value);
    if (status && status.value) params.set('status', status.value);
    if (page > 1) params.set('page', page);
    history.replaceState(null, '', siteURL(`/benchmarks/${benchmark}/tasks/`) + (params.size ? '?' + params : ''));
  }

  function render() {
    const terms = search.value.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
    const filtered = tasks.filter((q) => (!status || !status.value || q.status === status.value) &&
      terms.every((term) => q.search.includes(term)));
    const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
    page = Math.min(page, pages);
    const visible = filtered.slice((page-1)*pageSize, page*pageSize);
    const rows = visible.map((q) => {
      const url = escape(q.url);
      const label = q.status ? ` <span class="status status-${escape(q.status)}">${escape(q.status)}</span>` : '';
      return `<li><div class="entry-links"><a href="${url}">${escape(q.key)}</a>${label}</div><div class="entry-title"><a href="${url}">${escape(q.title)}</a></div></li>`;
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
    search.value = '';
    if (status) status.value = '';
    page = 1;
    render();
  }
  function scrollToResults() {
    $('.library-summary').scrollIntoView({block:'start',behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'});
  }
  let timer;
  search.addEventListener('input', () => {
    clearTimeout(timer);
    timer = setTimeout(() => { page = 1; render(); }, 120);
  });
  status?.addEventListener('change', () => { page = 1; render(); });
  $('[data-clear-tasks]').addEventListener('click', reset);
  $('#page-prev').addEventListener('click', () => { page--; render(); scrollToResults(); });
  $('#page-next').addEventListener('click', () => { page++; render(); scrollToResults(); });
  // Do not replace server-rendered tasks or react to controls until the index is ready.
  search.disabled = true;
  $('#page-next').disabled = true;
  fetch(siteURL(`/assets/tasks/${benchmark}.json`)).then((response) => {
    if (!response.ok) throw new Error('Task index could not be loaded');
    return response.json();
  }).then((data) => {
    tasks = data.map((q) => ({...q, search: [q.title,q.key,q.prompt].join(' ').toLocaleLowerCase()}));
    search.disabled = false;
    render();
  }).catch(() => {
    $('#task-count').innerHTML = `Search is unavailable. <a href="${escape(siteURL(`/benchmarks/${benchmark}/all-tasks/`))}">Browse all tasks instead →</a>`;
    $('.pagination').hidden = true;
  });
})();
