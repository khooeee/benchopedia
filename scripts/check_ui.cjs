/* Functional checks for browser enhancements without a browser dependency. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'assets', 'app.js'), 'utf8');
// Fixed fixtures cover one benchmark's task pages without depending on the
// imported catalog. Generated data and routes are checked by check_site.py.
function task(index, prompt = 'General fixture prompt') {
  const key = `alpha-${String(index).padStart(2, '0')}`;
  return {key, title:`Task ${key}`, prompt, url:`/benchmarks/alpha/tasks/${key}/`};
}
const data = Array.from({length:32}, (_, i) => task(i + 1));
data[0].prompt = 'sharedtoken context';
data[0].prompt_source_url = 'https://example.org/alpha/1';
data[30].prompt = 'sharedtoken context';

class Element {
  constructor(value = '', tagName = 'DIV') {
    Object.assign(this, {value, tagName, listeners:{}, disabled:false, hidden:false, checked:false, textContent:'', innerHTML:''});
  }
  addEventListener(event, action) { (this.listeners[event] ||= []).push(action); }
  emit(type, details = {}) {
    const event = {type, preventDefault(){this.defaultPrevented = true;}, ...details};
    this.dispatchEvent(event);
    return event;
  }
  dispatchEvent(event) { (this.listeners[event.type] || []).forEach((action) => action(event)); }
  scrollIntoView() {}
  focus() {}
}

async function library(search = '', fail = false, records = data, basePath = '', withStatus = false) {
  records = records.map((q) => ({...q, url:basePath + q.url}));
  const elements = Object.fromEntries([
    '#task-search','#task-results','#task-empty','#task-count','#page-status','#page-prev',
    '#page-next','.pagination','[data-clear-tasks]','.library-summary','.task-library',
    ...(withStatus ? ['#task-status'] : []),
  ].map((key) => [key, new Element()]));
  elements['meta[name="site-base-path"]'] = {content:basePath};
  elements['#task-search'].tagName = 'INPUT';
  elements['.task-library'].dataset = {benchmarkId:'alpha'};
  const context = {
    URLSearchParams, location:{search}, document:{querySelector:(key) => elements[key] || null,addEventListener(){}},
    history:{replaceState(_a,_b,url){context.url = url;}},
    fetch:async (url) => {context.fetchURL = url; return {ok:!fail,json:async () => records};},
    setTimeout(fn){fn();return 1;},clearTimeout(){},matchMedia:() => ({matches:true}),
  };
  vm.runInNewContext(source,context);
  await new Promise(setImmediate);
  return {elements,context};
}

function catalog(search = '', basePath = '') {
  const elements = Object.fromEntries([
    '#benchmark-search','#filter-solutions','#filter-tasks','#benchmark-count','#benchmark-empty',
    '#reset-benchmarks','.search-form',
  ].map((key) => [key, new Element()]));
  elements['meta[name="site-base-path"]'] = {content:basePath};
  const rows = ['alpha benchmark reasoning', 'beta benchmark coding', 'gamma benchmark reasoning'].map((search, index) => {
    const row = new Element();
    row.dataset = {search, hasSolutions:index === 0 ? 'true' : 'false', hasTasks:index < 2 ? 'true' : 'false'};
    return row;
  });
  const groups = rows.map((row) => {
    const group = new Element();
    group.querySelectorAll = () => [row];
    return group;
  });
  const context = {
    URLSearchParams,location:{search},
    document:{querySelector:(key) => elements[key] || null,querySelectorAll:(key) => key === '.year-group' ? groups : rows,addEventListener(){}},
    history:{replaceState(_a,_b,url){context.url = url;}},
  };
  vm.runInNewContext(source,context);
  return {elements,rows,groups,context};
}

function runTasks(search = '', results = ['pass', 'fail', 'fail']) {
  const elements = Object.fromEntries(['#result-filter', '#result-count'].map((key) => [key, new Element()]));
  const items = results.map((result) => Object.assign(new Element(), {dataset:{result}}));
  const context = {
    URLSearchParams, location:{search, pathname:'/benchmarks/alpha/runs/first/', hash:''},
    document:{querySelector:(key) => elements[key] || null, querySelectorAll:() => items, addEventListener(){}},
    history:{replaceState(_a,_b,url){context.url = url;}},
  };
  vm.runInNewContext(source, context);
  return {elements, items, context};
}

(async () => {
  const openElements = Object.fromEntries(['#open-filter', '#open-benchmark', '#open-count']
    .map((key) => [key, new Element()]));
  const openRows = ['alpha', 'beta', 'beta']
    .map((openBenchmark) => Object.assign(new Element(), {dataset:{openBenchmark}}));
  openElements['#open-filter'].hidden = true;
  vm.runInNewContext(source, {document:{
    querySelector:(key) => openElements[key] || null,
    querySelectorAll:() => openRows,
    addEventListener(){},
  }});
  assert.equal(openElements['#open-filter'].hidden, false);
  openElements['#open-benchmark'].value = 'beta';
  openElements['#open-benchmark'].emit('change');
  assert.deepEqual(openRows.map((row) => row.hidden), [true, false, false]);
  assert.equal(openElements['#open-count'].textContent, '2 tasks');
  openElements['#open-benchmark'].value = '';
  openElements['#open-benchmark'].emit('change');
  assert.ok(openRows.every((row) => !row.hidden));
  console.log('OK: Open tasks benchmark filter and counts');

  const run = runTasks('?result=fail');
  assert.equal(run.elements['#result-filter'].value, 'fail');
  assert.deepEqual(run.items.map((item) => item.hidden), [true, false, false]);
  assert.equal(run.elements['#result-count'].textContent, '2 tasks');
  assert.equal(run.context.url, '/benchmarks/alpha/runs/first/?result=fail');
  run.elements['#result-filter'].value = 'pass';
  run.elements['#result-filter'].emit('change');
  assert.deepEqual(run.items.map((item) => item.hidden), [false, true, true]);
  assert.equal(run.elements['#result-count'].textContent, '1 task');
  run.elements['#result-filter'].value = '';
  run.elements['#result-filter'].emit('change');
  assert.ok(run.items.every((item) => !item.hidden));
  assert.equal(run.context.url, '/benchmarks/alpha/runs/first/');
  assert.equal(runTasks('?result=maybe').elements['#result-filter'].value, '');
  const scoredRun = runTasks('?result=scored', ['scored', 'pending']);
  assert.equal(scoredRun.elements['#result-filter'].value, 'scored');
  assert.deepEqual(scoredRun.items.map((item) => item.hidden), [false, true]);
  assert.equal(scoredRun.elements['#result-count'].textContent, '1 task');
  console.log('OK: run task pass/fail filter, counts and URL state');
  const home = catalog('?q=alpha');
  assert.equal(home.elements['#benchmark-count'].textContent,'1 benchmark');
  assert.equal(home.rows[0].hidden,false);
  assert.equal(home.rows[1].hidden,true);
  home.elements['#benchmark-search'].value = 'no-such-benchmark';
  home.elements['#benchmark-search'].emit('input');
  assert.ok(home.groups.every((group) => group.hidden));
  assert.equal(home.elements['#benchmark-empty'].hidden,false);
  home.elements['#reset-benchmarks'].emit('click');
  assert.ok(home.groups.every((group) => !group.hidden));
  assert.equal(home.elements['#benchmark-count'].textContent,'3 benchmarks');
  assert.equal(home.context.url,'/');
  home.elements['#filter-solutions'].checked = true;
  home.elements['#filter-solutions'].emit('change');
  assert.equal(home.elements['#benchmark-count'].textContent, '1 benchmark');
  assert.equal(home.rows[0].hidden, false);
  assert.equal(home.rows[1].hidden, true);
  assert.equal(home.groups[1].hidden, true);
  assert.equal(home.context.url, '/?has_solutions=1');
  home.elements['#filter-solutions'].checked = false;
  home.elements['#filter-solutions'].emit('change');
  assert.ok(home.rows.every((row) => !row.hidden));
  assert.equal(home.elements['#benchmark-count'].textContent, '3 benchmarks');
  assert.equal(home.context.url, '/');
  const solutionsOnly = catalog('?q=alpha&has_solutions=1', '/benchopedia');
  assert.equal(solutionsOnly.elements['#filter-solutions'].checked, true);
  assert.equal(solutionsOnly.elements['#benchmark-count'].textContent, '1 benchmark');
  assert.equal(solutionsOnly.context.url, '/benchopedia/?q=alpha&has_solutions=1');
  solutionsOnly.elements['#benchmark-search'].value = 'beta';
  const submit = solutionsOnly.elements['.search-form'].emit('submit');
  assert.equal(submit.defaultPrevented, true);
  assert.equal(solutionsOnly.elements['#benchmark-count'].textContent, '0 benchmarks');
  assert.ok(solutionsOnly.groups.every((group) => group.hidden));
  assert.equal(solutionsOnly.elements['#benchmark-empty'].hidden, false);
  assert.equal(solutionsOnly.context.url, '/benchopedia/?q=beta&has_solutions=1');
  solutionsOnly.elements['#reset-benchmarks'].emit('click');
  assert.equal(solutionsOnly.elements['#filter-solutions'].checked, false);
  assert.equal(solutionsOnly.elements['#benchmark-search'].value, '');
  assert.ok(solutionsOnly.rows.every((row) => !row.hidden));
  assert.equal(solutionsOnly.elements['#benchmark-count'].textContent, '3 benchmarks');
  assert.equal(solutionsOnly.elements['#benchmark-empty'].hidden, true);
  assert.equal(solutionsOnly.context.url, '/benchopedia/');
  const withoutSolutionsFilter = catalog('?has_solutions=0');
  assert.equal(withoutSolutionsFilter.elements['#filter-solutions'].checked, false);
  assert.ok(withoutSolutionsFilter.rows.every((row) => !row.hidden));
  assert.equal(withoutSolutionsFilter.context.url, '/');
  const tasksOnly = catalog('?has_tasks=1', '/benchopedia');
  assert.equal(tasksOnly.elements['#filter-tasks'].checked, true);
  assert.deepEqual(tasksOnly.rows.map((row) => row.hidden), [false, false, true]);
  assert.equal(tasksOnly.groups[2].hidden, true);
  assert.equal(tasksOnly.elements['#benchmark-count'].textContent, '2 benchmarks');
  assert.equal(tasksOnly.context.url, '/benchopedia/?has_tasks=1');
  tasksOnly.elements['#filter-solutions'].checked = true;
  tasksOnly.elements['#filter-solutions'].emit('change');
  assert.deepEqual(tasksOnly.rows.map((row) => row.hidden), [false, true, true]);
  assert.equal(tasksOnly.context.url, '/benchopedia/?has_solutions=1&has_tasks=1');
  tasksOnly.elements['#benchmark-search'].value = 'gamma';
  tasksOnly.elements['#benchmark-search'].emit('input');
  assert.equal(tasksOnly.elements['#benchmark-empty'].hidden, false);
  assert.equal(tasksOnly.elements['#benchmark-count'].textContent, '0 benchmarks');
  tasksOnly.elements['#reset-benchmarks'].emit('click');
  assert.equal(tasksOnly.elements['#filter-tasks'].checked, false);
  assert.equal(tasksOnly.elements['#filter-solutions'].checked, false);
  assert.ok(tasksOnly.rows.every((row) => !row.hidden));
  assert.equal(tasksOnly.context.url, '/benchopedia/');
  tasksOnly.elements['#filter-tasks'].checked = true;
  tasksOnly.elements['#filter-tasks'].emit('change');
  assert.equal(tasksOnly.elements['#benchmark-count'].textContent, '2 benchmarks');
  tasksOnly.elements['#filter-tasks'].checked = false;
  tasksOnly.elements['#filter-tasks'].emit('change');
  assert.equal(tasksOnly.elements['#benchmark-count'].textContent, '3 benchmarks');
  const bothFilters = catalog('?q=alpha&has_solutions=1&has_tasks=1');
  assert.equal(bothFilters.elements['#filter-tasks'].checked, true);
  assert.equal(bothFilters.elements['#filter-solutions'].checked, true);
  assert.equal(bothFilters.elements['#benchmark-count'].textContent, '1 benchmark');
  const withoutTasksFilter = catalog('?has_tasks=0');
  assert.equal(withoutTasksFilter.elements['#filter-tasks'].checked, false);
  assert.ok(withoutTasksFilter.rows.every((row) => !row.hidden));
  assert.equal(withoutTasksFilter.context.url, '/');
  const {elements:e,context:c} = await library();
  assert.equal(c.fetchURL,'/assets/tasks/alpha.json');
  assert.equal(e['#task-search'].disabled,false);
  assert.equal(e['#task-count'].textContent,`1–25 of ${data.length} tasks`);
  assert.equal(e['#page-prev'].disabled,true);
  assert.ok(e['#task-results'].innerHTML.includes('href="/benchmarks/alpha/tasks/alpha-01/"'));
  assert.ok(!e['#task-results'].innerHTML.includes('Benchmark:'));
  assert.ok(!e['#task-results'].innerHTML.includes('>source</a>'));
  e['#page-next'].emit('click');
  assert.equal(e['#task-count'].textContent,`26–${data.length} of ${data.length} tasks`);
  assert.equal(e['#page-next'].disabled,true);
  assert.ok(e['#task-results'].innerHTML.includes('start="26"'));
  assert.equal(c.url,'/benchmarks/alpha/tasks/?page=2');
  e['#task-search'].value = 'sharedtoken';
  e['#task-search'].emit('input');
  assert.equal(e['#task-count'].textContent,'1–2 of 2 tasks');
  assert.ok(e['#task-results'].innerHTML.includes('alpha-01'));
  assert.ok(e['#task-results'].innerHTML.includes('alpha-31'));
  assert.equal(c.url,'/benchmarks/alpha/tasks/?q=sharedtoken');
  e['#task-search'].value = 'ALPHA-07';
  e['#task-search'].emit('input');
  assert.equal(e['#task-count'].textContent,'1–1 of 1 tasks');
  e['#task-search'].value = 'zzzz-no-such-prompt-zzzz';
  e['#task-search'].emit('input');
  assert.equal(e['#task-count'].textContent,'0 tasks');
  assert.equal(e['#task-empty'].hidden,false);
  assert.equal(e['.pagination'].hidden,true);
  e['[data-clear-tasks]'].emit('click');
  assert.equal(e['#task-search'].value,'');
  assert.equal(e['#task-count'].textContent,`1–25 of ${data.length} tasks`);
  assert.equal(c.url,'/benchmarks/alpha/tasks/');
  const deep = await library('?q=sharedtoken&page=999');
  assert.equal(deep.elements['#task-search'].value,'sharedtoken');
  assert.equal(deep.elements['#task-count'].textContent,'1–2 of 2 tasks');
  assert.equal(deep.elements['#page-status'].textContent,'Page 1 of 1');
  assert.equal(deep.context.url,'/benchmarks/alpha/tasks/?q=sharedtoken');
  const removedFilter = await library('?benchmark=beta');
  assert.equal(removedFilter.elements['#task-count'].textContent,`1–25 of ${data.length} tasks`);
  assert.equal(removedFilter.context.url,'/benchmarks/alpha/tasks/');
  const single = await library('',false,[task(1)]);
  assert.equal(single.elements['#task-count'].textContent,'1–1 of 1 tasks');
  assert.equal(single.elements['#page-next'].disabled,true);
  const empty = await library('',false,[]);
  assert.equal(empty.elements['#task-count'].textContent,'0 tasks');
  assert.equal(empty.elements['#task-empty'].hidden,false);
  const failed = await library('',true);
  assert.ok(failed.elements['#task-count'].innerHTML.includes('href="/benchmarks/alpha/all-tasks/"'));
  assert.equal(failed.elements['#task-search'].disabled, true);
  const project = await library('', false, data, '/benchopedia');
  assert.equal(project.context.fetchURL, '/benchopedia/assets/tasks/alpha.json');
  assert.equal(project.context.url, '/benchopedia/benchmarks/alpha/tasks/');
  assert.ok(project.elements['#task-results'].innerHTML.includes('href="/benchopedia/benchmarks/alpha/tasks/alpha-01/"'));
  project.elements['#page-next'].emit('click');
  assert.equal(project.context.url, '/benchopedia/benchmarks/alpha/tasks/?page=2');
  project.elements['#task-search'].value = 'sharedtoken';
  project.elements['#task-search'].emit('input');
  assert.equal(project.context.url, '/benchopedia/benchmarks/alpha/tasks/?q=sharedtoken');
  const projectFailure = await library('', true, data, '/benchopedia');
  assert.ok(projectFailure.elements['#task-count'].innerHTML.includes('href="/benchopedia/benchmarks/alpha/all-tasks/"'));
  const projectHome = catalog('?q=alpha', '/benchopedia');
  assert.equal(projectHome.context.url, '/benchopedia/?q=alpha');
  projectHome.elements['#reset-benchmarks'].emit('click');
  assert.equal(projectHome.context.url, '/benchopedia/');
  // Benchmarks with runs filter tasks by status; the others have no status control.
  assert.ok(!e['#task-results'].innerHTML.includes('class="status'));
  const statusData = data.map((q, i) => ({...q, status: i < 3 ? 'open' : i < 10 ? 'solved' : 'untested'}));
  const statuses = await library('?status=open', false, statusData, '', true);
  assert.equal(statuses.elements['#task-status'].value, 'open');
  assert.equal(statuses.elements['#task-count'].textContent, '1–3 of 3 tasks');
  assert.ok(statuses.elements['#task-results'].innerHTML.includes('<span class="status status-open">open</span>'));
  assert.ok(!statuses.elements['#task-results'].innerHTML.includes('status-solved'));
  assert.equal(statuses.context.url, '/benchmarks/alpha/tasks/?status=open');
  statuses.elements['#task-status'].value = 'solved';
  statuses.elements['#task-status'].emit('change');
  assert.equal(statuses.elements['#task-count'].textContent, '1–7 of 7 tasks');
  assert.equal(statuses.context.url, '/benchmarks/alpha/tasks/?status=solved');
  statuses.elements['#task-search'].value = 'ALPHA-04';
  statuses.elements['#task-search'].emit('input');
  assert.equal(statuses.elements['#task-count'].textContent, '1–1 of 1 tasks');
  assert.equal(statuses.context.url, '/benchmarks/alpha/tasks/?q=ALPHA-04&status=solved');
  statuses.elements['#task-status'].value = 'open';
  statuses.elements['#task-status'].emit('change');
  assert.equal(statuses.elements['#task-count'].textContent, '0 tasks');
  assert.equal(statuses.elements['#task-empty'].hidden, false);
  statuses.elements['[data-clear-tasks]'].emit('click');
  assert.equal(statuses.elements['#task-status'].value, '');
  assert.equal(statuses.elements['#task-count'].textContent, `1–25 of ${data.length} tasks`);
  assert.equal(statuses.context.url, '/benchmarks/alpha/tasks/');
  const unknownStatus = await library('?status=bogus', false, statusData, '/benchopedia', true);
  assert.equal(unknownStatus.elements['#task-status'].value, '');
  assert.equal(unknownStatus.elements['#task-count'].textContent, `1–25 of ${data.length} tasks`);
  assert.equal(unknownStatus.context.url, '/benchopedia/benchmarks/alpha/tasks/');
  const scoredTasks = await library('?status=scored', false, [{...task(1), status:'scored'}], '', true);
  assert.equal(scoredTasks.elements['#task-status'].value, 'scored');
  assert.ok(scoredTasks.elements['#task-results'].innerHTML.includes('status-scored'));
  console.log('OK: task status filter, status labels, URL state and reset');
  console.log('OK: project-path asset fetch, task links, pagination, search URLs and fallback');
  console.log('OK: benchmark tasks/solutions checkboxes, combined search, URL state, counts and reset');
  console.log('OK: per-benchmark task search, numbered task lists, empty/reset states, pagination, deep links and fetch failure fallback');
})().catch((error) => {console.error(error);process.exitCode = 1;});
