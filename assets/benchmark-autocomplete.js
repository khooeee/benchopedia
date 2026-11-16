/* A searchable, keyboard-accessible enhancement of the benchmark select. */
function createBenchmarkAutocomplete(select) {
  'use strict';
  const choices = [...select.options].map((option) => ({value:option.value, label:option.textContent}));
  const wrapper = document.createElement('span');
  wrapper.className = 'benchmark-autocomplete';
  const input = document.createElement('input');
  input.id = 'benchmark-autocomplete';
  input.type = 'text';
  input.autocomplete = 'off';
  input.placeholder = 'All benchmarks';
  input.setAttribute('role', 'combobox');
  input.setAttribute('aria-label', 'Benchmark');
  input.setAttribute('aria-autocomplete', 'list');
  input.setAttribute('aria-expanded', 'false');
  input.setAttribute('aria-controls', 'benchmark-options');
  const list = document.createElement('span');
  list.id = 'benchmark-options';
  list.className = 'benchmark-options';
  list.setAttribute('role', 'listbox');
  list.setAttribute('aria-label', 'Benchmarks');
  list.hidden = true;
  const status = document.createElement('span');
  status.className = 'benchmark-options benchmark-no-matches';
  status.setAttribute('role', 'status');
  status.textContent = 'No benchmarks match.';
  status.hidden = true;
  wrapper.append(input, list, status);
  select.insertAdjacentElement('afterend', wrapper);
  document.querySelector('label[for="filter-benchmark"]').htmlFor = input.id;
  select.hidden = true;
  let matches = [], active = -1;

  function close() {
    list.hidden = status.hidden = true;
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
    active = -1;
  }
  function sync() {
    input.value = choices.find((choice) => choice.value === select.value)?.label || '';
    close();
  }
  function choose(choice) {
    select.value = choice.value;
    sync();
    select.dispatchEvent(new Event('change', {bubbles:true}));
  }
  function show(query = '') {
    const term = query.trim().toLocaleLowerCase();
    matches = choices.filter((choice) => `${choice.label} ${choice.value}`.toLocaleLowerCase().includes(term));
    active = -1;
    input.removeAttribute('aria-activedescendant');
    list.replaceChildren();
    matches.forEach((choice, index) => {
      const option = document.createElement('span');
      option.id = `benchmark-option-${index}`;
      option.setAttribute('role', 'option');
      option.setAttribute('aria-selected', String(choice.value === select.value));
      option.textContent = choice.label;
      // Keep focus on the input so clicking a choice cannot trigger blur first.
      option.addEventListener('mousedown', (event) => event.preventDefault());
      option.addEventListener('click', () => choose(choice));
      list.append(option);
    });
    list.hidden = matches.length === 0;
    status.hidden = matches.length !== 0;
    input.setAttribute('aria-expanded', String(matches.length > 0));
  }
  function activate(index) {
    active = (index + matches.length) % matches.length;
    [...list.children].forEach((option, i) => option.classList.toggle('is-active', i === active));
    input.setAttribute('aria-activedescendant', list.children[active].id);
    list.children[active].scrollIntoView({block:'nearest'});
  }
  input.addEventListener('focus', () => { input.select(); show(); });
  input.addEventListener('click', () => { if (list.hidden && status.hidden) show(); });
  input.addEventListener('input', () => {
    show(input.value);
    if (!input.value.trim()) {
      select.value = '';
      select.dispatchEvent(new Event('change', {bubbles:true}));
    }
  });
  input.addEventListener('blur', sync);
  input.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      event.preventDefault();
      sync();
    } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault();
      if (list.hidden && status.hidden) show();
      if (matches.length) activate(active < 0 ? (event.key === 'ArrowDown' ? 0 : matches.length - 1) : active + (event.key === 'ArrowDown' ? 1 : -1));
    } else if (event.key === 'Enter' && !list.hidden) {
      event.preventDefault();
      if (matches.length) choose(matches[Math.max(0, active)]);
    }
  });
  sync();
  return {input, sync};
}
