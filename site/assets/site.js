(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('site-data').textContent);
  const menu = document.querySelector('.menu-toggle');
  const navigation = document.getElementById('navigation');
  function closeMenu() { navigation.classList.remove('open'); menu.setAttribute('aria-expanded', 'false'); }
  menu.addEventListener('click', () => { const open = navigation.classList.toggle('open'); menu.setAttribute('aria-expanded', String(open)); });
  navigation.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeMenu(); });

  const groupTabs = [...document.querySelectorAll('[data-group]')];
  function showGroup(button) {
    const group = data.groups[Number(button.dataset.group)];
    groupTabs.forEach(tab => {
      const selected = tab === button;
      tab.setAttribute('aria-selected', String(selected));
      tab.tabIndex = selected ? 0 : -1;
    });
    document.getElementById('group-panel').setAttribute('aria-labelledby', button.id);
    document.querySelector('[data-group-clock]').textContent = group.clock;
    document.querySelector('[data-group-period]').textContent = `${group.period} root ticks / window`;
    document.querySelectorAll('[data-window-labels] span').forEach((cell, i) => { cell.textContent = `${i * group.period}–${(i + 1) * group.period}`; });
    const rows = document.querySelector('[data-group-tracks]');
    rows.replaceChildren();
    group.tracks.forEach(track => {
      const row = document.createElement('div'); row.className = 'window-track';
      const label = document.createElement('div');
      const name = document.createElement('strong'); name.textContent = track.id;
      const detail = document.createElement('small'); detail.textContent = `${track.role} · ${track.direction}`;
      label.append(name, detail);
      const cells = document.createElement('div'); cells.className = 'window-cells';
      for (let i = 0; i < 4; i++) {
        const cell = document.createElement('span'); cell.className = 'window-cell'; cell.textContent = track.format;
        cells.append(cell);
      }
      row.append(label, cells); rows.append(row);
    });
    document.querySelector('[data-group-units]').textContent = group.units;
    document.querySelector('[data-group-queue]').textContent = group.queue;
    document.querySelector('[data-group-title]').textContent = group.id;
    document.querySelector('[data-group-description]').textContent = group.description;
  }
  groupTabs.forEach((button, index) => {
    button.addEventListener('click', () => showGroup(button));
    button.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % groupTabs.length;
      if (event.key === 'ArrowLeft') next = (index + groupTabs.length - 1) % groupTabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = groupTabs.length - 1;
      if (next !== undefined) { event.preventDefault(); groupTabs[next].focus(); showGroup(groupTabs[next]); }
    });
  });

  const code = document.querySelector('[data-code]');
  const tabs = [...document.querySelectorAll('[data-example]')];
  let selectedExample = 'clocks';
  function showExample(button) {
    selectedExample = button.dataset.example;
    tabs.forEach(tab => { const selected = tab === button; tab.setAttribute('aria-selected', String(selected)); tab.tabIndex = selected ? 0 : -1; });
    document.getElementById('code-panel').setAttribute('aria-labelledby', button.id);
    code.textContent = JSON.stringify(data.examples[selectedExample], null, 2);
  }
  tabs.forEach((button, index) => {
    button.addEventListener('click', () => showExample(button));
    button.addEventListener('keydown', event => {
      let next;
      if (event.key === 'ArrowRight') next = (index + 1) % tabs.length;
      if (event.key === 'ArrowLeft') next = (index + tabs.length - 1) % tabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = tabs.length - 1;
      if (next !== undefined) { event.preventDefault(); tabs[next].focus(); showExample(tabs[next]); }
    });
  });
  const copy = document.querySelector('[data-copy]');
  copy.addEventListener('click', async () => {
    try { await navigator.clipboard.writeText(JSON.stringify(data.examples[selectedExample], null, 2)); copy.textContent = data.copied; }
    catch { copy.textContent = data.copy_failed; }
    setTimeout(() => { copy.textContent = data.copy; }, 2000);
  });
})();
