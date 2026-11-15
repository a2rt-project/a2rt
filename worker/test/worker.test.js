import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { handle, embedding, rank, validatePayload } from '../src/index.js';

const origin = 'https://www.a2rt.org';
const payload = { question: 'What is sync_group_id?', language: 'en', currentPath: '/docs/en/', turnstileToken: 'test-token' };
const chunk = { title: 'Synchronization groups', section: 'Identity', content: 'sync_group_id identifies an independent synchronization group.', docs_url: '/en/overview.html', embedding: await embedding('sync_group_id independent synchronization group') };
function environment(overrides = {}) {
  return {
    AI_QA_ENABLED: 'true', AI_QA_API_KEY: 'fixture-only-model-secret', TURNSTILE_SECRET_KEY: 'fixture-only-challenge-secret',
    AI_QA_MODEL: 'fixture-model', AI_QA_BASE_URL: 'https://provider.invalid/v1', AI_QA_DOCS_URL_PREFIX: origin + '/docs', ALLOWED_ORIGIN: origin,
    ASSETS: { fetch: async () => Response.json([chunk]) }, AI_RATE_LIMITER: { limit: async () => ({ success: true }) }, ...overrides,
  };
}
function request(body = payload, options = {}) {
  return new Request('https://api.a2rt.org/api/ai-qa/chat', {
    method: 'POST', headers: { origin, 'Content-Type': 'application/json', 'CF-Connecting-IP': '192.0.2.1' }, body: JSON.stringify(body), ...options,
  });
}
function upstream(calls, verification = {}, modelStatus = 200) {
  return async (url, options) => {
    calls.push({ url: String(url), options });
    if (String(url).includes('siteverify')) return Response.json({ success: true, hostname: 'www.a2rt.org', action: 'docs_qa', ...verification });
    return modelStatus === 200 ? Response.json({ choices: [{ message: { content: 'sync_group_id identifies a synchronization group. [1]' } }] }) : new Response('sensitive provider error', { status: modelStatus });
  };
}

test('unconfigured deployment cannot call the provider', async () => {
  const response = await handle(request(), environment({ AI_QA_ENABLED: 'false' }), { fetch: () => assert.fail('Network must not run') });
  assert.equal(response.status, 503);
  assert.deepEqual(await response.json(), { error: 'AI_NOT_CONFIGURED' });
});
test('CORS preflight permits only the configured website', async () => {
  const response = await handle(request(undefined, { method: 'OPTIONS', body: undefined }), environment());
  assert.equal(response.status, 204);
  assert.equal(response.headers.get('Access-Control-Allow-Origin'), origin);
  const rejected = await handle(request(payload, { headers: { origin: 'https://elsewhere.invalid' } }), environment());
  assert.equal(rejected.status, 403);
  assert.equal(rejected.headers.get('Access-Control-Allow-Origin'), null);
});
test('missing rate limiter fails closed; rate limit rejects before provider use', async () => {
  assert.equal((await handle(request(), environment({ AI_RATE_LIMITER: undefined }))).status, 503);
  const response = await handle(request(), environment({ AI_RATE_LIMITER: { limit: async () => ({ success: false }) } }), { fetch: () => assert.fail('No provider use') });
  assert.equal(response.status, 429);
  assert.equal(response.headers.get('Retry-After'), '60');
});
test('browser cannot supply provider URL, model, system prompt, or credentials', () => {
  for (const field of ['base_url', 'model', 'messages', 'api_key']) {
    assert.throws(() => validatePayload({ ...payload, [field]: 'attacker-value' }), /UNKNOWN_FIELD/);
  }
  assert.throws(() => validatePayload({ ...payload, language: '../../secret' }), /INVALID_LANGUAGE/);
  assert.throws(() => validatePayload({ ...payload, question: 'a'.repeat(1201) }), /INVALID_QUESTION/);
});
test('body size is enforced on actual bytes even without Content-Length', async () => {
  const response = await handle(request({ ...payload, question: 'a'.repeat(20000) }), environment());
  assert.equal(response.status, 413);
});
test('Turnstile success, expected hostname, and action are all required', async () => {
  for (const verification of [{ success: false }, { success: 'true' }, { success: 1 }, { hostname: 'evil.invalid' }, { hostname: 'localhost' }, { action: 'something_else' }]) {
    const calls = [];
    const response = await handle(request(), environment(), { fetch: upstream(calls, verification) });
    assert.equal(response.status, 403);
    assert.equal(calls.length, 1);
  }
});
test('missing Turnstile secret or token cannot reach the model', async () => {
  const neverFetch = () => assert.fail('Unverified requests must not call the network');
  assert.equal((await handle(request(), environment({ TURNSTILE_SECRET_KEY: '' }), { fetch: neverFetch })).status, 503);
  const response = await handle(request({ ...payload, turnstileToken: '' }), environment(), { fetch: neverFetch });
  assert.equal(response.status, 400);
  assert.deepEqual(await response.json(), { error: 'CHALLENGE_REQUIRED' });
});
test('Siteverify replay rejection prevents a second model call', async () => {
  const used = new Set();
  let modelCalls = 0;
  const fetcher = async (url, options) => {
    if (String(url).includes('siteverify')) {
      const token = JSON.parse(options.body).response;
      if (used.has(token)) return Response.json({ success: false, 'error-codes': ['timeout-or-duplicate'] });
      used.add(token);
      return Response.json({ success: true, hostname: 'www.a2rt.org', action: 'docs_qa' });
    }
    modelCalls++;
    return Response.json({ choices: [{ message: { content: 'A2RT documentation answer.' } }] });
  };
  assert.equal((await handle(request(), environment(), { fetch: fetcher })).status, 200);
  const replay = await handle(request(), environment(), { fetch: fetcher });
  assert.equal(replay.status, 403);
  assert.deepEqual(await replay.json(), { error: 'CHALLENGE_FAILED' });
  assert.equal(modelCalls, 1);
});
test('upstream redirects are rejected without forwarding credentials', async () => {
  for (const redirectTarget of ['siteverify', 'model']) {
    let calls = 0;
    const response = await handle(request(), environment(), {
      fetch: async (url, options) => {
        calls++;
        assert.equal(options.redirect, 'manual');
        if (redirectTarget === 'siteverify' || !String(url).includes('siteverify')) {
          return new Response(null, { status: 307, headers: { Location: 'https://elsewhere.invalid/collect' } });
        }
        return Response.json({ success: true, hostname: 'www.a2rt.org', action: 'docs_qa' });
      },
    });
    assert.equal(response.status, redirectTarget === 'siteverify' ? 503 : 502);
    assert.equal(calls, redirectTarget === 'siteverify' ? 1 : 2);
  }
});
test('question is grounded in built docs; model credential stays upstream', async () => {
  const calls = [];
  const response = await handle(request(), environment(), { fetch: upstream(calls) });
  assert.equal(response.status, 200);
  const body = await response.json();
  assert.equal(body.sources[0].url, origin + '/docs/en/overview.html');
  const model = calls.find(call => call.url.includes('provider.invalid'));
  assert.equal(model.url, 'https://provider.invalid/v1/chat/completions');
  assert.equal(model.options.headers.Authorization, 'Bearer fixture-only-model-secret');
  assert.equal(model.options.redirect, 'manual');
  const sent = JSON.parse(model.options.body);
  assert.match(sent.messages[0].content, /2026-11-16 architecture design draft/);
  assert.match(sent.messages[0].content, /not a released wire format/);
  assert.equal(sent.stream, false);
  assert.equal(sent.max_tokens, 1024);
  assert.match(sent.messages[1].content, /independent synchronization group/);
  assert.doesNotMatch(JSON.stringify(body), /fixture-only|test-token/);
});
test('provider errors are sanitized and carry no key or provider response body', async () => {
  const response = await handle(request(), environment(), { fetch: upstream([], {}, 401) });
  assert.equal(response.status, 502);
  assert.deepEqual(await response.json(), { error: 'MODEL_UNAVAILABLE' });
});
test('DeepSeek uses non-thinking mode without changing other providers', async () => {
  for (const base of ['https://api.deepseek.com', 'https://provider.invalid/v1']) {
    const calls = [];
    const response = await handle(request(), environment({ AI_QA_BASE_URL: base, AI_QA_MODEL: 'deepseek-flash' }), { fetch: upstream(calls) });
    assert.equal(response.status, 200);
    const sent = JSON.parse(calls[1].options.body);
    assert.equal(sent.model, 'deepseek-flash');
    if (base === 'https://api.deepseek.com') assert.deepEqual(sent.thinking, { type: 'disabled' });
    else assert.equal(sent.thinking, undefined);
  }
});
test('server rejects credentials in upstream URLs', async () => {
  const calls = [];
  const response = await handle(request(), environment({ AI_QA_BASE_URL: 'https://user:pass@provider.invalid/v1' }), { fetch: upstream(calls) });
  assert.equal(response.status, 503);
  assert.equal(calls.length, 1);
});
test('Worker hashing matches the actual Python-generated index', async () => {
  const chunks = JSON.parse(await readFile(new URL('../assets/index/chunks_zh.json', import.meta.url)));
  for (const chunk of chunks.slice(0, 3)) {
    const vector = await embedding(`${chunk.title}\n${chunk.section}\n${chunk.content}`);
    vector.forEach((value, index) => assert.ok(Math.abs(value - chunk.embedding[index]) < 0.000001));
  }
});


test('health identifies the current architecture without claiming a wire release', async () => {
  const response = await handle(new Request('https://api.a2rt.org/api/ai-qa/healthz'), environment());
  const body = await response.json();
  assert.equal(body.protocol, 'A2RT');
  assert.equal(body.documentation, 'architecture-draft');
  assert.equal(body.revision, '2026-11-16');
});

test('bilingual retrieval finds current single-frame and system-group rules', async () => {
  for (const [language, question, expectedSource, evidence] of [
    ['zh', 'system 轨道必须独立成组吗？', '04-system-track-and-lifecycle', /同组|同一.*组|独立.*组/],
    ['zh', '每轨每周期最多一个数据帧是什么意思？', '01-clock-sync-group-track-model', /每条轨道每个周期最多只能有一个数据帧/],
    ['en', 'Can both directions publish a data frame in the same period on a bidirectional track?', '01-clock-sync-group-track-model', /only one data frame|at most one data frame/],
    ['en', 'What are Core and Profile responsibilities?', '03-core-profile-responsibilities', /Profile Content events and schemas/],
  ]) {
    const chunks = JSON.parse(await readFile(new URL(`../assets/index/chunks_${language}.json`, import.meta.url)));
    const results = (await rank(question, chunks)).slice(0, 3);
    assert.ok(results.some(result => result.source_path.includes(expectedSource) && evidence.test(result.content)), question);
  }
});
