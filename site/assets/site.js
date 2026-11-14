(() => {
  'use strict';
  const data = JSON.parse(document.getElementById('site-data').textContent);
  const menu = document.querySelector('.menu-toggle');
  const navigation = document.getElementById('navigation');
  function closeMenu() { navigation.classList.remove('open'); menu.setAttribute('aria-expanded', 'false'); }
  menu.addEventListener('click', () => { const open = navigation.classList.toggle('open'); menu.setAttribute('aria-expanded', String(open)); });
  navigation.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
  document.addEventListener('keydown', event => { if (event.key === 'Escape') closeMenu(); });

  document.querySelectorAll('[data-track]').forEach(button => button.addEventListener('click', () => {
    document.querySelectorAll('[data-track]').forEach(item => { item.classList.remove('selected'); item.setAttribute('aria-pressed', 'false'); });
    button.classList.add('selected'); button.setAttribute('aria-pressed', 'true');
    const track = data.tracks[Number(button.dataset.track)];
    document.querySelector('[data-track-title]').textContent = track.id;
    document.querySelector('[data-track-description]').textContent = track.description;
  }));

  const playButton = document.querySelector('.play-toggle');
  const grid = document.querySelector('.track-grid');
  const clock = document.querySelector('.console-clock');
  const motion = matchMedia('(prefers-reduced-motion: reduce)');
  let playing = !motion.matches, elapsed = 0, previous = 0, frame;
  function updateButton() {
    const label = playing ? playButton.dataset.pause : playButton.dataset.play;
    playButton.setAttribute('aria-label', label);
    document.querySelector('[data-play-label]').textContent = label;
    document.querySelector('[data-play-icon]').textContent = playing ? 'Ⅱ' : '▷';
  }
  function tick(now) {
    if (!playing || document.hidden) { previous = 0; return; }
    if (previous) elapsed = (elapsed + Math.min(now - previous, 100)) % 3000;
    previous = now;
    grid.style.setProperty('--progress', (elapsed / 3000).toFixed(4));
    clock.textContent = '00:0' + (elapsed / 1000).toFixed(2);
    frame = requestAnimationFrame(tick);
  }
  function start() { cancelAnimationFrame(frame); previous = 0; if (playing && !document.hidden) frame = requestAnimationFrame(tick); }
  playButton.addEventListener('click', () => { playing = !playing; updateButton(); start(); });
  document.addEventListener('visibilitychange', start);
  motion.addEventListener('change', () => { if (motion.matches) { playing = false; updateButton(); start(); } });
  updateButton(); start();

  const code = document.querySelector('[data-code]');
  const tabs = [...document.querySelectorAll('[data-example]')];
  let selectedExample = 'output';
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
