(() => {
  'use strict';
  const toggle = document.querySelector('[data-site-menu]');
  const navigation = document.getElementById('site-navigation');
  const breakpoint = matchMedia('(max-width: 767px)');
  function closeMenu(restoreFocus = false) {
    navigation.classList.remove('is-open');
    toggle.setAttribute('aria-expanded', 'false');
    if (restoreFocus) toggle.focus();
  }
  toggle.addEventListener('click', () => {
    const open = navigation.classList.toggle('is-open');
    toggle.setAttribute('aria-expanded', String(open));
  });
  navigation.addEventListener('click', event => { if (event.target.closest('a')) closeMenu(); });
  document.addEventListener('click', event => { if (!event.target.closest('.site-header')) closeMenu(); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && navigation.classList.contains('is-open')) closeMenu(true);
  });
  document.addEventListener('focusin', event => { if (!event.target.closest('.site-header')) closeMenu(); });
  breakpoint.addEventListener('change', () => closeMenu());
  const modifier = document.querySelector('[data-shortcut-modifier]');
  if (modifier && !/Mac|iPhone|iPad/.test(navigator.platform)) modifier.textContent = 'Ctrl';
})();
