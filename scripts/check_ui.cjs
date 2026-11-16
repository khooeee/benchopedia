/* Functional checks for browser enhancements without a browser dependency. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'assets/app.js'), 'utf8');
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
    Object.assign(this, {value, tagName, listeners:{}, disabled:false, hidden:false, textContent:'', innerHTML:'', options:[]});
    this.classList = {remove(){},toggle(){}};
  }
  addEventListener(event, action) { this.listeners[event] = action; }
  emit(event) { return this.listeners[event]?.({}); }
  scrollIntoView() {}
  focus() {}
}

async function library(search = '', fail = false, records = data) {
  const elements = Object.fromEntries([
    '#task-search','#filter-benchmark',
    '#task-results','#task-empty','#task-count','#page-status','#page-prev',
    '#page-next','.pagination','#clear-filters','[data-clear-tasks]','.library-summary',
  ].map((key) => [key, new Element()]));
  elements['#task-search'].tagName = 'INPUT';
  for (const [key, values] of Object.entries({
    '#filter-benchmark':['',...new Set(records.map((q) => q.benchmark_id))],
  })) {
    elements[key].tagName = 'SELECT';
    elements[key].value = values[0];
    elements[key].options = values.map((value) => ({value}));
  }
  const context = {
    URLSearchParams, location:{search}, document:{querySelector:(key) => elements[key] || null,addEventListener(){}},
    history:{replaceState(_a,_b,url){context.url = url;}},
    fetch:async () => ({ok:!fail,json:async () => records}),
    setTimeout(fn){fn();return 1;},clearTimeout(){},matchMedia:() => ({matches:true}),
  };
  vm.runInNewContext(source,context);
  await new Promise(setImmediate);
  return {elements,context};
}

function catalog(search = '') {
  const elements = Object.fromEntries([
    '#benchmark-search','#benchmark-count','#benchmark-empty',
    '#reset-benchmarks','.search-form',
  ].map((key) => [key, new Element()]));
  const rows = ['alpha benchmark reasoning', 'beta benchmark coding'].map((search) => {
    const row = new Element();
    row.dataset = {search};
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
  e['#filter-benchmark'].value = 'beta';
  e['#filter-benchmark'].emit('change');
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
  const deep = await library('?benchmark=beta&q=general&page=999');
  assert.equal(deep.elements['#task-count'].textContent,'1–1 of 1 tasks');
  assert.equal(deep.elements['#page-status'].textContent,'Page 1 of 1');
  assert.ok(deep.elements['#task-results'].innerHTML.includes('Task beta-02'));
  assert.ok(deep.elements['#task-results'].innerHTML.includes('Benchmark: <a href="/benchmarks/beta/">beta benchmark</a>'));
  assert.ok(!deep.elements['#task-results'].innerHTML.includes('alpha-01'));
  deep.elements['#task-search'].value = 'no-match';
  deep.elements['#task-search'].emit('input');
  assert.equal(deep.elements['#task-count'].textContent,'0 tasks');
  deep.elements['#clear-filters'].emit('click');
  assert.equal(deep.elements['#task-count'].textContent,`1–25 of ${data.length} tasks`);
  const single = await library('',false,[task('small', 1)]);
  assert.equal(single.elements['#task-count'].textContent,'1–1 of 1 tasks');
  assert.equal(single.elements['#page-next'].disabled,true);
  const empty = await library('',false,[]);
  assert.equal(empty.elements['#task-count'].textContent,'0 tasks');
  assert.equal(empty.elements['#task-empty'].hidden,false);
  const failed = await library('',true);
  assert.ok(failed.elements['#task-count'].innerHTML.includes('/tasks/all/'));
  console.log('OK: benchmark search, numbered task lists, combined filters, empty/reset states, pagination, deep links and fetch failure fallback');
})().catch((error) => {console.error(error);process.exitCode = 1;});
