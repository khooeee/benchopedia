/* Functional checks for browser enhancements without a browser dependency. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'assets/app.js'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(root, 'dist/assets/tasks.json')));

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
  const row = new Element();
  row.dataset = {search:'swe-bench verified real github issues'};
  const group = new Element();
  group.querySelectorAll = () => [row];
  const context = {
    URLSearchParams,location:{search},
    document:{querySelector:(key) => elements[key] || null,querySelectorAll:(key) => key === '.year-group' ? [group] : [row],addEventListener(){}},
    history:{replaceState(_a,_b,url){context.url = url;}},
  };
  vm.runInNewContext(source,context);
  return {elements,row,group,context};
}

(async () => {
  const home = catalog('?q=verified');
  assert.equal(home.elements['#benchmark-count'].textContent,'1 benchmark');
  assert.equal(home.row.hidden,false);
  home.elements['#benchmark-search'].value = 'no-such-benchmark';
  home.elements['#benchmark-search'].emit('input');
  assert.equal(home.group.hidden,true);
  assert.equal(home.elements['#benchmark-empty'].hidden,false);
  home.elements['#reset-benchmarks'].emit('click');
  assert.equal(home.group.hidden,false);
  assert.equal(home.context.url,'/');
  const {elements:e,context:c} = await library();
  assert.equal(e['#task-count'].textContent,'1–25 of 500 tasks');
  assert.equal(e['#page-prev'].disabled,true);
  assert.ok(e['#task-results'].innerHTML.includes('Benchmark: <a href="/benchmarks/swe-bench-verified/">SWE-bench Verified</a>'));
  assert.ok(!e['#task-results'].innerHTML.includes('>source</a>'));
  e['#page-next'].emit('click');
  assert.equal(e['#task-count'].textContent,'26–50 of 500 tasks');
  assert.ok(e['#task-results'].innerHTML.includes('start="26"'));
  assert.equal(c.url,'/tasks/?page=2');
  e['#task-search'].value = 'separability_matrix';
  e['#task-search'].emit('input');
  assert.ok(e['#task-results'].innerHTML.includes('astropy__astropy-12907'));
  assert.ok(!e['#task-results'].innerHTML.includes('django__django'));
  e['#task-search'].value = 'zzzz-no-such-prompt-zzzz';
  e['#task-search'].emit('input');
  assert.equal(e['#task-count'].textContent,'0 tasks');
  assert.equal(e['#task-empty'].hidden,false);
  e['[data-clear-tasks]'].emit('click');
  assert.equal(e['#task-count'].textContent,'1–25 of 500 tasks');
  const other = {benchmark_id:'another-benchmark',benchmark_name:'Another benchmark',benchmark_url:'/benchmarks/another-benchmark/',key:'example-1',title:'Example task',prompt:'Example prompt',url:'/example-1/'};
  const deep = await library('?benchmark=another-benchmark&page=999',false,[...data,other]);
  assert.equal(deep.elements['#task-count'].textContent,'1–1 of 1 tasks');
  assert.equal(deep.elements['#page-status'].textContent,'Page 1 of 1');
  assert.ok(deep.elements['#task-results'].innerHTML.includes('Example task'));
  assert.ok(deep.elements['#task-results'].innerHTML.includes('Benchmark: <a href="/benchmarks/another-benchmark/">Another benchmark</a>'));
  assert.ok(!deep.elements['#task-results'].innerHTML.includes('astropy__astropy-12907'));
  deep.elements['#task-search'].value = 'no-match';
  deep.elements['#task-search'].emit('input');
  assert.equal(deep.elements['#task-count'].textContent,'0 tasks');
  deep.elements['#clear-filters'].emit('click');
  assert.equal(deep.elements['#task-count'].textContent,'1–25 of 501 tasks');
  const failed = await library('',true);
  assert.ok(failed.elements['#task-count'].innerHTML.includes('/tasks/all/'));
  console.log('OK: benchmark search, numbered task lists, combined filters, empty/reset states, pagination, deep links and fetch failure fallback');
})().catch((error) => {console.error(error);process.exitCode = 1;});
