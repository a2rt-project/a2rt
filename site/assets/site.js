(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('site-data').textContent);
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
    document.querySelector('[data-group-track-count]').textContent = `${group.tracks.length} ${group.tracks.length === 1 ? data.track_label : data.tracks_label}`;
    const rows = document.querySelector('[data-group-tracks]');
    rows.replaceChildren();
    group.tracks.forEach(track => {
      const chip = document.createElement('span'); chip.textContent = track.id;
      rows.append(chip);
    });
    document.querySelector('[data-group-description]').textContent = group.description;
  }
  groupTabs.forEach((button, index) => {
    button.addEventListener('click', () => showGroup(button));
    button.addEventListener('keydown', event => {
      let next;
      if (['ArrowRight', 'ArrowDown'].includes(event.key)) next = (index + 1) % groupTabs.length;
      if (['ArrowLeft', 'ArrowUp'].includes(event.key)) next = (index + groupTabs.length - 1) % groupTabs.length;
      if (event.key === 'Home') next = 0;
      if (event.key === 'End') next = groupTabs.length - 1;
      if (next !== undefined) { event.preventDefault(); groupTabs[next].focus(); showGroup(groupTabs[next]); }
    });
  });

  // One 6-second sweep represents 100 root ticks, slowed for legibility.
  // All lanes share this time coordinate; no completion or delivery is implied.
  const illustration = document.querySelector('.rhythm');
  const motion = document.querySelector('[data-motion-toggle]');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  let playing = !reducedMotion.matches;
  let inView = true;
  function syncMotion() {
    illustration.dataset.motion = playing && inView && !document.hidden ? 'playing' : 'paused';
    motion.setAttribute('aria-pressed', String(playing));
    motion.setAttribute('aria-label', playing ? data.pause_motion : data.play_motion);
    motion.querySelector('[data-motion-label]').textContent = playing ? data.pause_motion : data.play_motion;
  }
  motion.addEventListener('click', () => { playing = !playing; syncMotion(); });
  reducedMotion.addEventListener('change', () => { playing = !reducedMotion.matches; syncMotion(); });
  document.addEventListener('visibilitychange', syncMotion);
  if ('IntersectionObserver' in window) {
    new IntersectionObserver(entries => { inView = entries[0].isIntersecting; syncMotion(); }).observe(illustration);
  }
  syncMotion();

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
