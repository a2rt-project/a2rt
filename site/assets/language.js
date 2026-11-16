(() => {
  'use strict';
  const preferenceKey = 'a2rt.language';
  const valid = value => value === 'en' || value === 'zh';

  // A language link is an explicit choice, including keyboard/new-tab clicks.
  const remember = event => {
    const link = event.target.closest?.('a[data-site-language]');
    const language = link?.dataset.siteLanguage;
    if (!valid(language) || (event.type === 'auxclick' && event.button !== 1)) return;
    try { localStorage.setItem(preferenceKey, language); } catch (_) { /* Storage may be disabled. */ }
  };
  document.addEventListener('click', remember);
  document.addEventListener('auxclick', remember);

  // Only neutral entry pages select a language. Explicit language URLs never redirect.
  const { siteBase: base, languageEntry: entry } = document.documentElement.dataset;
  if (!base || !['home', 'docs'].includes(entry)) return;
  let language;
  try { language = localStorage.getItem(preferenceKey); } catch (_) { /* Use browser preference. */ }
  if (!valid(language)) {
    const preferred = navigator.languages?.[0] || navigator.language || 'en';
    language = /^zh(?:[-_]|$)/i.test(preferred) ? 'zh' : 'en';
  }
  // English is already the static homepage; it also works without JavaScript.
  if (entry === 'home' && language === 'en') return;
  const target = entry === 'docs' ? `${base}docs/${language}/` : `${base}zh/`;
  location.replace(target + location.search + location.hash);
})();
