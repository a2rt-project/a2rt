"""Shared navigation and search copy for the landing pages and Sphinx."""
from copy import deepcopy

_UI_TEXT = {
    "zh": {
        "breadcrumb": "面包屑",
        "copy_markdown": "Copy Markdown",
        "documentation_source": "文档源码",
        "home": "首页",
        "in_this_article": "本文目录",
        "language": "语言",
        "language_menu": "选择语言",
        "next": "下一篇",
        "open_sidebar": "打开侧栏",
        "page_toc": "本页目录",
        "prev_next": "上一/下一篇",
        "previous": "上一篇",
        "ai_search": "AI 搜索",
        "ai_search_empty": "请先输入要查询的问题。",
        "ai_search_error": "AI 搜索服务暂不可用，请稍后重试。",
        "ai_search_loading": "正在根据文档生成回答…",
        "ai_search_verifying": "请完成安全验证，验证后将开始生成回答。",
        "ai_search_no_sources": "未在当前文档中找到可靠来源。",
        "ai_search_retention_notice": "回答由 AI 根据文档生成，请核对引用来源。问题会发送给配置的模型服务。",
        "ai_search_sources": "参考来源",
        "ai_label": "AI",
        "ask_ai": "Ask AI",
        "close_search": "关闭搜索",
        "search_or_ask": "Search or ask",
        "search_or_ask_ai": "Search or ask AI",
        "search_docs": "搜索文档",
        "search_placeholder": "Search",
        "sidebar": "侧栏导航",
    },
    "en": {
        "breadcrumb": "Breadcrumb",
        "copy_markdown": "Copy Markdown",
        "documentation_source": "Documentation source",
        "home": "Home",
        "in_this_article": "In this article",
        "language": "Language",
        "language_menu": "Select language",
        "next": "Next",
        "open_sidebar": "Open sidebar",
        "page_toc": "Page contents",
        "prev_next": "Previous/next article",
        "previous": "Previous",
        "ai_search": "AI Search",
        "ai_search_empty": "Enter a question first.",
        "ai_search_error": "AI Search is unavailable. Try again later.",
        "ai_search_loading": "Generating an answer from the docs…",
        "ai_search_verifying": "Complete the security check to start generating your answer.",
        "ai_search_no_sources": "No reliable source was found in the current docs.",
        "ai_search_retention_notice": "AI answers may be inaccurate. Check cited documentation. Questions are sent to the configured model provider.",
        "ai_search_sources": "Sources",
        "ai_label": "AI",
        "ask_ai": "Ask AI",
        "close_search": "Close search",
        "search_or_ask": "Search or ask",
        "search_or_ask_ai": "Search or ask AI",
        "search_docs": "Search docs",
        "search_placeholder": "Search",
        "sidebar": "Sidebar navigation",
    },
}
_SEARCH_EXAMPLES = {
    "zh": ["根时钟与同步组是什么关系？", "每轨每周期最多一个数据帧是什么意思？", "谁发送谁负责，模型需要处理重传吗？", "Core 是否强制错误通知或 ACK？"],
    "en": ["How do root clocks and sync groups relate?", "What does one data frame per track per period mean?", "Who prepares information and handles send-side recovery?", "Does Core require error notifications or ACKs?"],
}

def shell_context(config, language, page=None):
    base = config["base_path"]
    home = base + ("en/" if language == "en" else "")
    docs = base + f"docs/{language}/"
    other = "en" if language == "zh" else "zh"
    enabled = bool(config["ai_endpoint"] and config["turnstile_site_key"])
    ui = deepcopy(_UI_TEXT[language])
    examples = _SEARCH_EXAMPLES[language]
    if not enabled:
        label = "搜索文档" if language == "zh" else "Search docs"
        ui.update(search_or_ask=label, search_or_ask_ai=label, ai_label="", ask_ai=label)
        examples = ["根时钟", "同步组", "system", "media_type"] if language == "zh" else ["root clock", "sync groups", "system", "media_type"]
    return {
        "site_nav": {
            "base": base, "home": home, "docs": docs, "is_docs": page is not None,
            "repo": config["repository"], "search": ui["search_docs"],
            "protocol": "协议" if language == "zh" else "Protocol",
            "architecture": "架构" if language == "zh" else "Architecture",
            "label": "网站导航" if language == "zh" else "Main navigation",
            "menu": "展开导航" if language == "zh" else "Toggle navigation",
            "alternate": base + f"docs/{other}/{page}.html" if page is not None else base + ("en/" if other == "en" else ""),
            "other": other, "language_label": "English" if other == "en" else "切换为中文",
        },
        "search_action": docs + "search.html", "ps_ui": ui,
        "ps_current_language": {"code": language, "html_lang": "zh-CN" if language == "zh" else "en"},
        "ps_search_examples": examples, "a2rt_ai_enabled": enabled,
        "a2rt_ai_endpoint": config["ai_endpoint"], "a2rt_turnstile_site_key": config["turnstile_site_key"],
    }
