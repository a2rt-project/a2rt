/* Browser-local keyword search over the same public document chunks as Q&A. */
(async () => {
  const zh = document.documentElement.lang.startsWith('zh');
  const status = document.querySelector('[data-search-status]');
  const results = document.querySelector('[data-search-results]');
  const input = document.querySelector('.a2rt-search-form input');
  const question = new URLSearchParams(location.search).get('q')?.trim() || '';
  input.value = question;
  if (!question) { status.textContent = zh ? '输入关键词开始搜索。' : 'Enter a keyword to search.'; return; }
  status.textContent = zh ? '正在搜索文档…' : 'Searching the docs…';
  try {
    const response = await fetch(document.querySelector('meta[name="a2rt-search-index"]').content);
    if (!response.ok) throw new Error('Index unavailable');
    const chunks = await response.json();
    const query = question.toLowerCase().slice(0, 300);
    const terms = query.match(/[a-z0-9_]+|[\u4e00-\u9fff]+/gu) || [query];
    const prefix = document.querySelector('meta[name="a2rt-docs-prefix"]').content;
    const pages = new Map();
    for (const chunk of chunks) {
      const title = `${chunk.title} ${chunk.section}`.toLowerCase();
      const text = chunk.content.toLowerCase();
      const score = (title.includes(query) ? 12 : 0) + (text.includes(query) ? 6 : 0) + terms.reduce((sum, term) => sum + (title.includes(term) ? 4 : 0) + (text.includes(term) ? 1 : 0), 0);
      if (!score || !/^\/(zh|en)\//.test(chunk.docs_url) || chunk.docs_url.includes('..')) continue;
      const key = chunk.docs_url.split('#')[0];
      if (!pages.has(key) || pages.get(key).score < score) pages.set(key, { ...chunk, score });
    }
    const matches = [...pages.values()].sort((a, b) => b.score - a.score);
    status.textContent = matches.length ? (zh ? `找到 ${matches.length} 篇相关文档` : `${matches.length} matching documents`) : (zh ? '未找到匹配内容。请尝试更短的关键词。' : 'No results. Try a shorter keyword.');
    for (const item of matches) {
      const article = document.createElement('article');
      article.className = 'a2rt-search-result';
      const title = document.createElement('h2');
      const link = document.createElement('a');
      link.href = prefix + item.docs_url;
      link.textContent = item.title;
      title.append(link);
      const section = document.createElement('div');
      section.className = 'a2rt-search-section';
      section.textContent = item.section;
      const excerpt = document.createElement('p');
      const first = Math.max(0, item.content.toLowerCase().indexOf(query) - 50);
      excerpt.textContent = (first ? '…' : '') + item.content.slice(first, first + 230) + (item.content.length > first + 230 ? '…' : '');
      article.append(title, section, excerpt);
      results.append(article);
    }
  } catch {
    status.textContent = zh ? '搜索索引暂时无法加载，请刷新重试，或使用侧栏浏览。' : 'The search index could not be loaded. Reload or browse the sidebar.';
  }
})();
