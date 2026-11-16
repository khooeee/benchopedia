/* Functional checks for browser enhancements without a browser dependency. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const source = fs.readFileSync(path.join(root, 'web/assets/app.js'), 'utf8');
const data = JSON.parse(fs.readFileSync(path.join(root, 'dist/assets/questions.json')));

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
    '#question-search','#filter-benchmark','#question-sort',
    '#question-results','#question-empty','#question-count','#page-status','#page-prev',
    '#page-next','.pagination','#clear-filters','[data-clear-questions]','.library-summary',
  ].map((key) => [key, new Element()]));
  elements['#question-search'].tagName = 'INPUT';
  for (const [key, values] of Object.entries({
    '#filter-benchmark':['',...new Set(records.map((q) => q.benchmark_id))],
    '#question-sort':['id','title'],
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
    '#benchmark-search','#benchmark-category','#benchmark-count','#benchmark-empty',
    '#reset-benchmarks','.search-form',
  ].map((key) => [key, new Element()]));
  elements['#benchmark-category'].options = [{value:''},{value:'Software engineering'}];
  const row = new Element();
  row.dataset = {category:'Software engineering',search:'swe-bench verified software engineering real github issues'};
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
  const home = catalog('?q=verified&category=Software+engineering');
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
  assert.equal(e['#question-count'].textContent,'1–25 of 500 questions');
  assert.equal(e['#page-prev'].disabled,true);
  e['#page-next'].emit('click');
  assert.equal(e['#question-count'].textContent,'26–50 of 500 questions');
  assert.ok(e['#question-results'].innerHTML.includes('start="26"'));
  assert.equal(c.url,'/questions/?page=2');
  e['#question-search'].value = 'separability_matrix';
  e['#question-search'].emit('input');
  assert.ok(e['#question-results'].innerHTML.includes('astropy__astropy-12907'));
  assert.ok(!e['#question-results'].innerHTML.includes('django__django'));
  e['#question-search'].value = 'zzzz-no-such-prompt-zzzz';
  e['#question-search'].emit('input');
  assert.equal(e['#question-count'].textContent,'0 questions');
  assert.equal(e['#question-empty'].hidden,false);
  e['[data-clear-questions]'].emit('click');
  assert.equal(e['#question-count'].textContent,'1–25 of 500 questions');
  e['#question-sort'].value = 'title';
  e['#question-sort'].emit('change');
  const first = [...data].sort((a,b) => a.title.localeCompare(b.title))[0];
  assert.ok(e['#question-results'].innerHTML.indexOf(first.url) >= 0);
  const other = {benchmark_id:'another-benchmark',key:'example-1',title:'Example task',prompt:'Example prompt',url:'/example-1/'};
  const deep = await library('?benchmark=another-benchmark&page=999',false,[...data,other]);
  assert.equal(deep.elements['#question-count'].textContent,'1–1 of 1 questions');
  assert.equal(deep.elements['#page-status'].textContent,'Page 1 of 1');
  assert.ok(deep.elements['#question-results'].innerHTML.includes('Example task'));
  assert.ok(!deep.elements['#question-results'].innerHTML.includes('astropy__astropy-12907'));
  deep.elements['#question-search'].value = 'no-match';
  deep.elements['#question-search'].emit('input');
  assert.equal(deep.elements['#question-count'].textContent,'0 questions');
  deep.elements['#clear-filters'].emit('click');
  assert.equal(deep.elements['#question-count'].textContent,'1–25 of 501 questions');
  const failed = await library('',true);
  assert.ok(failed.elements['#question-count'].innerHTML.includes('/questions/all/'));
  console.log('OK: benchmark search/categories, numbered question lists, combined filters, empty/reset states, sorting, pagination, deep links and fetch failure fallback');
})().catch((error) => {console.error(error);process.exitCode = 1;});
