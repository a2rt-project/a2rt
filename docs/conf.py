from __future__ import annotations

import os
import json
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from markupsafe import Markup

# -- Project information -----------------------------------------------------

project = "A2RT"
author = "A2RT Project"
copyright = f"{datetime.now().year}, {author}"
release = "0.2 draft"

_LANGUAGE_ALIASES = {
    "zh": "zh_CN",
    "zh-CN": "zh_CN",
    "zh_CN": "zh_CN",
    "en": "en",
    "en-US": "en",
}
language = _LANGUAGE_ALIASES.get(os.environ.get("DOCS_LANGUAGE", "zh_CN"), "zh_CN")
_LANGUAGE_CODE = "en" if language.startswith("en") else "zh"
_LANGUAGE_LABELS = {
    "zh": {"label": "中文", "html_lang": "zh-CN", "sphinx_language": "zh_CN"},
    "en": {"label": "English", "html_lang": "en", "sphinx_language": "en"},
}
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
        "ai_search_loading": "正在根据文档生成回答...",
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
        "ai_search_loading": "Generating an answer from the docs...",
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
    "zh": ["A2RT 的六条轨道分别是什么？", "事件窗口和操作名额有什么区别？", "如何理解 accepted 和 completed？", "如何处理视觉晚于音频到达？"],
    "en": ["What are the six logical tracks?", "How do event windows differ from operation limits?", "Does accepted mean completed?", "How are late visuals handled?"],
}
_CONFIG = json.loads(os.environ["A2RT_SITE_CONFIG"])
_AI_ENABLED = bool(_CONFIG["ai_endpoint"] and _CONFIG["turnstile_site_key"])
if not _AI_ENABLED:
    _SEARCH_EXAMPLES = {"zh": ["轨道", "回执", "执行策略", "event_id"], "en": ["tracks", "receipts", "execution policy", "event_id"]}
    for code, label in [("zh", "搜索文档"), ("en", "Search docs")]:
        _UI_TEXT[code].update(search_or_ask=label, search_or_ask_ai=label, ai_label="", ask_ai=label)



def _format_toc_section_count(section_count: int) -> str:
    if _LANGUAGE_CODE == "en":
        return f"This article has {section_count} section" if section_count == 1 else f"This article has {section_count} sections"
    return f"本文共 {section_count} 节"


def _build_toc_intro_context(context: dict[str, object]) -> None:
    raw_toc = str(context.get("toc") or "").strip()
    fallback_title = str(context.get("title") or "")
    next_page = context.get("next")
    intro = {
        "title": fallback_title,
        "section_count": 0,
        "section_count_display": _format_toc_section_count(0),
        "next": next_page,
    }

    context["ps_toc_intro"] = intro
    context["ps_toc_html"] = Markup(raw_toc)

    if not raw_toc:
        return

    try:
        wrapper = ET.fromstring(f"<div>{raw_toc}</div>")
    except ET.ParseError:
        return

    root_ul = wrapper.find("ul")
    if root_ul is None:
        return

    root_li = root_ul.find("li")
    if root_li is None:
        return

    title_link = root_li.find("a")
    if title_link is not None:
        toc_title = "".join(title_link.itertext()).strip()
        if toc_title:
            intro["title"] = toc_title

    child_ul = root_li.find("ul")
    if child_ul is None:
        context["ps_toc_html"] = Markup("")
        return

    section_count = len(child_ul.findall("li"))
    intro["section_count"] = section_count
    intro["section_count_display"] = _format_toc_section_count(section_count)
    context["ps_toc_html"] = Markup(ET.tostring(child_ul, encoding="unicode", method="html"))


def setup(app):
    app.connect("html-page-context", lambda app, pagename, templatename, context, doctree: _build_toc_intro_context(context))
    return {
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }

# -- General configuration ---------------------------------------------------

extensions = [
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
]

templates_path = []
exclude_patterns = ["Thumbs.db", ".DS_Store"]
locale_dirs = []
gettext_compact = True
source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

# -- HTML output: in-repo psdocs theme ---------------------------------------

_THEME_DIR = Path(__file__).resolve().parent / "theme"
html_theme_path = [str(_THEME_DIR)]
html_theme = "psdocs"

html_title = "A2RT Documentation" if _LANGUAGE_CODE == "en" else "A2RT 协议文档"
html_short_title = "A2RT Docs"
html_baseurl = f"{_CONFIG['origin']}{_CONFIG['base_path']}docs/{_LANGUAGE_CODE}/"
html_favicon = str(Path(__file__).parent / "static/favicon.svg")
html_static_path = [str(Path(__file__).parent / "static")]
html_css_files = ["a2rt.css"]
html_search_language = "en" if _LANGUAGE_CODE == "en" else "zh"
html_copy_source = True
html_show_sphinx = False
html_show_sourcelink = False
html_show_search_summary = False
_BREADCRUMB_SECTIONS = {"zh": {}, "en": {}}
html_context = {
    "asset_version": "a2rt-02",
    "a2rt_base": _CONFIG["base_path"],
    "a2rt_home": _CONFIG["base_path"] + ("en/" if _LANGUAGE_CODE == "en" else ""),
    "a2rt_ai_enabled": _AI_ENABLED,
    "a2rt_ai_endpoint": _CONFIG["ai_endpoint"],
    "a2rt_turnstile_site_key": _CONFIG["turnstile_site_key"],
    "breadcrumb_sections": _BREADCRUMB_SECTIONS[_LANGUAGE_CODE],
    "ps_current_language": _LANGUAGE_LABELS[_LANGUAGE_CODE] | {"code": _LANGUAGE_CODE},
    "ps_languages": [
        _LANGUAGE_LABELS["zh"] | {"code": "zh"},
        _LANGUAGE_LABELS["en"] | {"code": "en"},
    ],
    "ps_search_examples": _SEARCH_EXAMPLES[_LANGUAGE_CODE],
    "ps_ui": _UI_TEXT[_LANGUAGE_CODE],
}

# psdocs ships app.js under its static/; theme.conf already declares stylesheets.
html_js_files = ["js/app.js"]

# psdocs theme options (string values; see theme/psdocs/theme.conf)
html_theme_options = {
    "brand_name": "A2RT Docs",
    "brand_short": "Docs",
    "sidebar_title": "A2RT / 0.2 DRAFT",
    "repo_url": "https://github.com/a2rt-project/a2rt",
    "show_copy_md": "true",
    "banner_text": "0.2 草案 · 规范与示例，不是生产 SDK。" if _LANGUAGE_CODE == "zh" else "Draft 0.2 · Specification and examples, not a production SDK.",
    "banner_link_label": "",
    "banner_link_url": "",
}

# Sidebar template list (sidebar.html is provided by psdocs partials but
# the basic theme expects entries in html_sidebars). We render the sidebar
# directly inside layout.html, so leave this empty to suppress default basic
# sidebars (localtoc + relations + sourcelink + searchbox).
html_sidebars: dict[str, list[str]] = {"**": []}

# -- MyST / Copybutton -------------------------------------------------------

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "substitution",
    "tasklist",
]

copybutton_prompt_text = r">>> |\.\.\. |\$ |PS> "
copybutton_prompt_is_regexp = True
