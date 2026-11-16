import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { runInNewContext } from 'node:vm';
import test from 'node:test';

const script = await readFile(new URL('../../site/assets/language.js', import.meta.url), 'utf8');

function visit({ entry = 'home', base = '/', languages = ['en-US'], language = 'en-US', preference = null, blocked = false, search = '', hash = '', storage = new Map() } = {}) {
  if (preference !== null) storage.set('a2rt.language', preference);
  const handlers = {};
  const redirects = [];
  runInNewContext(script, {
    document: {
      documentElement: { dataset: { siteBase: base, languageEntry: entry } },
      addEventListener: (type, callback) => { handlers[type] = callback; },
    },
    navigator: { languages, language },
    localStorage: {
      getItem: key => { if (blocked) throw new Error('Storage disabled'); return storage.get(key); },
      setItem: (key, value) => { if (blocked) throw new Error('Storage disabled'); storage.set(key, value); },
    },
    location: { search, hash, replace: target => redirects.push(target) },
  });
  return { redirects, storage, choose: (lang, type = 'click', button = 0) => handlers[type]({ type, button, target: { closest: () => ({ dataset: { siteLanguage: lang } }) } }) };
}

test('neutral homepage selects Chinese variants and leaves all other preferred languages in English', () => {
  for (const language of ['zh', 'zh-CN', 'zh-TW', 'zh-Hant-HK', 'ZH_cn']) {
    assert.deepEqual(visit({ languages: [language] }).redirects, ['/zh/']);
  }
  for (const languages of [['en-US'], ['fr-FR', 'zh-CN'], ['ja'], []]) {
    assert.deepEqual(visit({ languages }).redirects, []);
  }
  assert.deepEqual(visit({ languages: [], language: 'zh-CN' }).redirects, ['/zh/']);
});

test('neutral docs entry routes to the chosen language while retaining query and anchor', () => {
  for (const base of ['/', '/a2rt/']) {
    for (const language of ['zh', 'en']) {
      assert.deepEqual(visit({ entry: 'docs', base, languages: [language], search: '?q=clock', hash: '#main' }).redirects,
        [`${base}docs/${language}/?q=clock#main`]);
    }
    assert.deepEqual(visit({ base, languages: ['zh'], hash: '#architecture' }).redirects, [`${base}zh/#architecture`]);
  }
});

test('saved manual preference wins over the browser across homepage and docs', () => {
  const page = visit({ entry: '', languages: ['zh'] });
  page.choose('en');
  assert.equal(page.storage.get('a2rt.language'), 'en');
  assert.deepEqual(visit({ languages: ['zh'], storage: page.storage }).redirects, []);
  assert.deepEqual(visit({ entry: 'docs', languages: ['zh'], storage: page.storage }).redirects, ['/docs/en/']);
  page.choose('zh');
  assert.deepEqual(visit({ languages: ['en'], storage: page.storage }).redirects, ['/zh/']);
});

test('explicit language pages never redirect, regardless of browser or saved preference', () => {
  for (const preference of ['en', 'zh']) {
    for (const language of ['en', 'zh']) {
      assert.deepEqual(visit({ entry: '', languages: [language], preference }).redirects, []);
    }
  }
});

test('disabled or invalid storage falls back safely and does not break explicit language links', () => {
  assert.deepEqual(visit({ blocked: true, languages: ['zh'] }).redirects, ['/zh/']);
  assert.deepEqual(visit({ preference: 'invalid', languages: ['zh'] }).redirects, ['/zh/']);
  const page = visit({ entry: '', blocked: true, languages: ['zh'] });
  assert.doesNotThrow(() => page.choose('en'));
  assert.deepEqual(page.redirects, []);
});

test('language links remember new-tab choices and ignore invalid values or right-clicks', () => {
  const page = visit({ entry: '' });
  page.choose('zh', 'auxclick', 1);
  assert.equal(page.storage.get('a2rt.language'), 'zh');
  page.choose('en', 'auxclick', 2);
  page.choose('invalid');
  assert.equal(page.storage.get('a2rt.language'), 'zh');
});
