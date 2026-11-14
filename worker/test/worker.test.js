import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { handle, embedding, validatePayload } from '../src/index.js';

const origin = 'https://www.a2rt.org';
const payload = { question: 'What is event_id?', language: 'en', currentPath: '/docs/en/', turnstileToken: 'test-token' };
const chunk = { title: 'Events', section: 'Receipts', content: 'event_id associates execution receipts with an event.', docs_url: '/en/overview.html', embedding: await embedding('event_id execution receipts') };
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
    return modelStatus === 200 ? Response.json({ choices: [{ message: { content: 'A receipt references event_id. [1]' } }] }) : new Response('sensitive provider error', { status: modelStatus });
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
  for (const verification of [{ success: false }, { hostname: 'evil.invalid' }, { action: 'something_else' }]) {
    const calls = [];
    const response = await handle(request(), environment(), { fetch: upstream(calls, verification) });
    assert.equal(response.status, 403);
    assert.equal(calls.length, 1);
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
  assert.equal(model.options.redirect, 'error');
  const sent = JSON.parse(model.options.body);
  assert.equal(sent.stream, false);
  assert.equal(sent.max_tokens, 1024);
  assert.match(sent.messages[1].content, /execution receipts/);
  assert.doesNotMatch(JSON.stringify(body), /fixture-only|test-token/);
});
test('provider errors are sanitized and carry no key or provider response body', async () => {
  const response = await handle(request(), environment(), { fetch: upstream([], {}, 401) });
  assert.equal(response.status, 502);
  assert.deepEqual(await response.json(), { error: 'MODEL_UNAVAILABLE' });
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
