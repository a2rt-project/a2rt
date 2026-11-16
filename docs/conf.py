from __future__ import annotations

import os
import json
import hashlib
import sys
from datetime import datetime
from pathlib import Path
from xml.etree import ElementTree as ET

from markupsafe import Markup

# -- Project information -----------------------------------------------------

project = "A2RT"
author = "A2RT Project"
copyright = f"{datetime.now().year}, {author}"
release = "Architecture draft · 2026-11-16"

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
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))
from site_ui import shell_context
_CONFIG = json.loads(os.environ["A2RT_SITE_CONFIG"])



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
    app.connect("html-page-context", lambda app, pagename, templatename, context, doctree: context.update(shell_context(_CONFIG, _LANGUAGE_CODE, pagename)))
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

templates_path = [str(_ROOT / "site")]
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
# Keep cached theme assets until their content changes, including local previews.
_ASSET_HASH = hashlib.sha256()
for _asset_root in (_THEME_DIR / "psdocs/static", Path(__file__).parent / "static", _ROOT / "site/assets"):
    for _asset in sorted(_asset_root.rglob("*")):
        if _asset.is_file():
            _ASSET_HASH.update(_asset.relative_to(_asset_root).as_posix().encode() + b"\0")
            _ASSET_HASH.update(_asset.read_bytes())
html_context = {
    "asset_version": _ASSET_HASH.hexdigest()[:16],
    "a2rt_base": _CONFIG["base_path"],
    "a2rt_home": _CONFIG["base_path"] + ("en/" if _LANGUAGE_CODE == "en" else ""),
    "a2rt_ai_endpoint": _CONFIG["ai_endpoint"],
    "a2rt_turnstile_site_key": _CONFIG["turnstile_site_key"],
    "breadcrumb_sections": _BREADCRUMB_SECTIONS[_LANGUAGE_CODE],
    "ps_current_language": _LANGUAGE_LABELS[_LANGUAGE_CODE] | {"code": _LANGUAGE_CODE},
    "ps_languages": [
        _LANGUAGE_LABELS["zh"] | {"code": "zh"},
        _LANGUAGE_LABELS["en"] | {"code": "en"},
    ],
}

# psdocs ships app.js under its static/; theme.conf already declares stylesheets.
html_js_files = ["js/app.js"]

# psdocs theme options (string values; see theme/psdocs/theme.conf)
html_theme_options = {
    "brand_name": "A2RT Docs",
    "brand_short": "Docs",
    "sidebar_title": "A2RT / ARCHITECTURE DRAFT",
    "repo_url": "https://github.com/a2rt-project/a2rt",
    "show_copy_md": "true",
    "banner_text": "架构设计草案 · 2026-11-16 · 新线协议与运行时尚未发布。" if _LANGUAGE_CODE == "zh" else "Architecture draft · 2026-11-16 · New wire version and runtime not yet released.",
    "banner_link_label": "",
    "banner_link_url": "",
}

# Sidebar template list (sidebar.html is provided by psdocs partials but
# the basic theme expects entries in html_sidebars). We render the sidebar
# directly inside layout.html, so leave this empty to suppress default basic
# sidebars (localtoc + relations + sourcelink + searchbox).
html_sidebars: dict[str, list[str]] = {"**": []}

# -- MyST / Copybutton -------------------------------------------------------

myst_heading_anchors = 4

myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "substitution",
    "tasklist",
]

copybutton_prompt_text = r">>> |\.\.\. |\$ |PS> "
copybutton_prompt_is_regexp = True
