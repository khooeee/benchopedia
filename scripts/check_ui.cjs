/* Functional checks for browser enhancements without a browser dependency. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const source = ['benchmark-autocomplete.js', 'app.js'].map((file) => fs.readFileSync(path.join(root, 'assets', file), 'utf8')).join('\n');
// Fixed fixtures cover multiple benchmarks and pages without depending on the
// imported catalog. Generated data and routes are checked by check_site.py.
function task(benchmark, index, prompt = 'General fixture prompt') {
  const key = `${benchmark}-${String(index).padStart(2, '0')}`;
  return {
    benchmark_id:benchmark, benchmark_name:`${benchmark} benchmark`,
    benchmark_url:`/benchmarks/${benchmark}/`, key, title:`Task ${key}`, prompt,
    url:`/benchmarks/${benchmark}/tasks/${key}/`,
  };
}
const data = [
  ...Array.from({length:30}, (_, i) => task('alpha', i + 1)),
  task('beta', 1, 'sharedtoken context'), task('beta', 2),
];
data[0].prompt = 'sharedtoken context';
data[0].prompt_source_url = 'https://example.org/alpha/1';

class Element {
  constructor(value = '', tagName = 'DIV') {
    Object.assign(this, {value, tagName, listeners:{}, disabled:false, hidden:false, checked:false, textContent:'', innerHTML:'', options:[], children:[], attributes:{}});
    this.classList = {remove(){},toggle(){}};
  }
  addEventListener(event, action) { (this.listeners[event] ||= []).push(action); }
  emit(type, details = {}) {
    const event = {type, preventDefault(){this.defaultPrevented = true;}, ...details};
    this.dispatchEvent(event);
    return event;
  }
  dispatchEvent(event) { (this.listeners[event.type] || []).forEach((action) => action(event)); }
  setAttribute(name, value) { this.attributes[name] = value; }
  removeAttribute(name) { delete this.attributes[name]; }
  append(...elements) { this.children.push(...elements); }
  replaceChildren(...elements) { this.children = elements; }
  insertAdjacentElement(_position, element) { this.after = element; }
  select() {}
  scrollIntoView() {}
  focus() {}
}

async function library(search = '', fail = false, records = data, basePath = '') {
  records = records.map((q) => ({...q, url:basePath + q.url, benchmark_url:basePath + q.benchmark_url}));
  const elements = Object.fromEntries([
    '#task-search','#filter-benchmark','label[for="filter-benchmark"]',
    '#task-results','#task-empty','#task-count','#page-status','#page-prev',
    '#page-next','.pagination','[data-clear-tasks]','.library-summary',
  ].map((key) => [key, new Element()]));
  elements['meta[name="site-base-path"]'] = {content:basePath};
  elements['#task-search'].tagName = 'INPUT';
  for (const [key, values] of Object.entries({
    '#filter-benchmark':['',...new Set(records.map((q) => q.benchmark_id))],
  })) {
    elements[key].tagName = 'SELECT';
    elements[key].value = values[0];
    elements[key].options = values.map((value) => ({value, textContent:value ? `${value} benchmark` : 'All benchmarks'}));
  }
  const context = {
    URLSearchParams, Event, location:{search}, document:{querySelector:(key) => elements[key] || null,createElement:(tag) => new Element('',tag.toUpperCase()),addEventListener(){}},
    history:{replaceState(_a,_b,url){context.url = url;}},
    fetch:async (url) => {context.fetchURL = url; return {ok:!fail,json:async () => records};},
    setTimeout(fn){fn();return 1;},clearTimeout(){},matchMedia:() => ({matches:true}),
  };
  vm.runInNewContext(source,context);
  await new Promise(setImmediate);
  [elements.autocomplete, elements.suggestions, elements.autocompleteStatus] = elements['#filter-benchmark'].after.children;
  return {elements,context};
}

function catalog(search = '', basePath = '') {
  const elements = Object.fromEntries([
    '#benchmark-search','#filter-solutions','#benchmark-count','#benchmark-empty',
    '#reset-benchmarks','.search-form',
  ].map((key) => [key, new Element()]));
  elements['meta[name="site-base-path"]'] = {content:basePath};
  const rows = ['alpha benchmark reasoning', 'beta benchmark coding'].map((search, index) => {
    const row = new Element();
    row.dataset = {search, hasSolutions:index === 0 ? 'true' : 'false'};
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

(async () => {
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
  assert.equal(home.elements['#benchmark-count'].textContent,'2 benchmarks');
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
  assert.equal(home.elements['#benchmark-count'].textContent, '2 benchmarks');
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
  assert.equal(solutionsOnly.elements['#benchmark-count'].textContent, '2 benchmarks');
  assert.equal(solutionsOnly.elements['#benchmark-empty'].hidden, true);
  assert.equal(solutionsOnly.context.url, '/benchopedia/');
  const withoutSolutionsFilter = catalog('?has_solutions=0');
  assert.equal(withoutSolutionsFilter.elements['#filter-solutions'].checked, false);
  assert.ok(withoutSolutionsFilter.rows.every((row) => !row.hidden));
  assert.equal(withoutSolutionsFilter.context.url, '/');
  const {elements:e,context:c} = await library();
  assert.equal(e['#task-count'].textContent,`1–25 of ${data.length} tasks`);
  assert.equal(e['#page-prev'].disabled,true);
  assert.ok(e['#task-results'].innerHTML.includes('Benchmark: <a href="/benchmarks/alpha/">alpha benchmark</a>'));
  assert.ok(!e['#task-results'].innerHTML.includes('>source</a>'));
  e['#page-next'].emit('click');
  assert.equal(e['#task-count'].textContent,`26–${data.length} of ${data.length} tasks`);
  assert.equal(e['#page-next'].disabled,true);
  assert.ok(e['#task-results'].innerHTML.includes('start="26"'));
  assert.equal(c.url,'/tasks/?page=2');
  e['#task-search'].value = 'sharedtoken';
  e['#task-search'].emit('input');
  assert.equal(e['#task-count'].textContent,'1–2 of 2 tasks');
  assert.ok(e['#task-results'].innerHTML.includes('alpha-01'));
  assert.ok(e['#task-results'].innerHTML.includes('beta-01'));
  e.autocomplete.emit('focus');
  assert.equal(e.suggestions.children.length, 3);
  e.autocomplete.value = 'BeTa';
  e.autocomplete.emit('input');
  assert.equal(e.suggestions.children.length, 1);
  assert.equal(e.suggestions.children[0].textContent, 'beta benchmark');
  e.autocomplete.emit('keydown', {key:'ArrowDown'});
  assert.equal(e.autocomplete.attributes['aria-activedescendant'], e.suggestions.children[0].id);
  e.autocomplete.emit('keydown', {key:'Enter'});
  assert.equal(e['#filter-benchmark'].value, 'beta');
  assert.equal(e.autocomplete.value, 'beta benchmark');
  assert.equal(e.suggestions.hidden, true);
  assert.equal(c.url, '/tasks/?q=sharedtoken&benchmark=beta');
  assert.equal(e['#task-count'].textContent,'1–1 of 1 tasks');
  assert.ok(e['#task-results'].innerHTML.includes('beta-01'));
  assert.ok(!e['#task-results'].innerHTML.includes('alpha-01'));
  e['#task-search'].value = 'zzzz-no-such-prompt-zzzz';
  e['#task-search'].emit('input');
  assert.equal(e['#task-count'].textContent,'0 tasks');
  assert.equal(e['#task-empty'].hidden,false);
  e['[data-clear-tasks]'].emit('click');
  assert.equal(e['#task-count'].textContent,`1–25 of ${data.length} tasks`);
  assert.equal(e['#filter-benchmark'].value,'');
  assert.equal(e.autocomplete.value, 'All benchmarks');
  const deep = await library('?benchmark=beta&q=general&page=999');
  assert.equal(deep.elements['#task-count'].textContent,'1–1 of 1 tasks');
  assert.equal(deep.elements['#page-status'].textContent,'Page 1 of 1');
  assert.equal(deep.elements.autocomplete.value, 'beta benchmark');
  assert.ok(deep.elements['#task-results'].innerHTML.includes('Task beta-02'));
  assert.ok(deep.elements['#task-results'].innerHTML.includes('Benchmark: <a href="/benchmarks/beta/">beta benchmark</a>'));
  assert.ok(!deep.elements['#task-results'].innerHTML.includes('alpha-01'));
  deep.elements['#task-search'].value = 'no-match';
  deep.elements['#task-search'].emit('input');
  assert.equal(deep.elements['#task-count'].textContent,'0 tasks');
  deep.elements['[data-clear-tasks]'].emit('click');
  assert.equal(deep.elements['#task-count'].textContent,`1–25 of ${data.length} tasks`);
  e.autocomplete.emit('focus');
  e.autocomplete.value = 'no such benchmark';
  e.autocomplete.emit('input');
  assert.equal(e.autocompleteStatus.hidden, false);
  assert.equal(e.suggestions.hidden, true);
  e.autocomplete.emit('keydown', {key:'Enter'});
  assert.equal(e['#filter-benchmark'].value, '');
  e.autocomplete.emit('keydown', {key:'Escape'});
  assert.equal(e.autocomplete.value, 'All benchmarks');
  assert.equal(e.autocompleteStatus.hidden, true);
  e.autocomplete.emit('focus');
  e.autocomplete.value = 'beta';
  e.autocomplete.emit('input');
  e.suggestions.children[0].emit('click');
  assert.equal(e['#task-count'].textContent, '1–2 of 2 tasks');
  e.autocomplete.emit('focus');
  e.autocomplete.value = 'unfinished';
  e.autocomplete.emit('input');
  e.autocomplete.emit('blur');
  assert.equal(e.autocomplete.value, 'beta benchmark');
  e.autocomplete.value = '';
  e.autocomplete.emit('input');
  assert.equal(e['#filter-benchmark'].value, '');
  assert.equal(e['#task-count'].textContent, `1–25 of ${data.length} tasks`);
  assert.equal(c.url, '/tasks/');
  e.autocomplete.emit('keydown', {key:'ArrowUp'});
  e.autocomplete.emit('keydown', {key:'Enter'});
  assert.equal(e['#filter-benchmark'].value, 'beta');
  const unknown = await library('?benchmark=unknown');
  assert.equal(unknown.elements.autocomplete.value, 'All benchmarks');
  assert.equal(unknown.context.url, '/tasks/');
  const single = await library('',false,[task('small', 1)]);
  assert.equal(single.elements['#task-count'].textContent,'1–1 of 1 tasks');
  assert.equal(single.elements['#page-next'].disabled,true);
  const empty = await library('',false,[]);
  assert.equal(empty.elements['#task-count'].textContent,'0 tasks');
  assert.equal(empty.elements['#task-empty'].hidden,false);
  const failed = await library('',true);
  assert.ok(failed.elements['#task-count'].innerHTML.includes('/tasks/all/'));
  assert.equal(failed.elements.autocomplete.disabled, true);
  const project = await library('', false, data, '/benchopedia');
  assert.equal(project.context.fetchURL, '/benchopedia/assets/tasks.json');
  assert.equal(project.context.url, '/benchopedia/tasks/');
  assert.ok(project.elements['#task-results'].innerHTML.includes('href="/benchopedia/benchmarks/alpha/tasks/alpha-01/"'));
  assert.ok(project.elements['#task-results'].innerHTML.includes('href="/benchopedia/benchmarks/alpha/"'));
  project.elements['#page-next'].emit('click');
  assert.equal(project.context.url, '/benchopedia/tasks/?page=2');
  project.elements['#task-search'].value = 'sharedtoken';
  project.elements['#task-search'].emit('input');
  assert.equal(project.context.url, '/benchopedia/tasks/?q=sharedtoken');
  const projectFailure = await library('', true, data, '/benchopedia');
  assert.ok(projectFailure.elements['#task-count'].innerHTML.includes('href="/benchopedia/tasks/all/"'));
  const projectHome = catalog('?q=alpha', '/benchopedia');
  assert.equal(projectHome.context.url, '/benchopedia/?q=alpha');
  projectHome.elements['#reset-benchmarks'].emit('click');
  assert.equal(projectHome.context.url, '/benchopedia/');
  console.log('OK: project-path asset fetch, task links, pagination, search URLs and fallback');
  console.log('OK: benchmark solution checkbox, combined search, URL state, counts and reset');
  console.log('OK: benchmark search/autocomplete, numbered task lists, combined filters, empty/reset states, pagination, deep links and fetch failure fallback');
})().catch((error) => {console.error(error);process.exitCode = 1;});
