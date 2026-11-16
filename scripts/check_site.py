"""Check built HTML links, fragments, assets, and accidental credential exposure."""
from __future__ import annotations
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
from urllib.parse import unquote, urljoin, urlsplit

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
BASE = "/" + os.environ.get("SITE_BASE_PATH", json.loads((ROOT / "site.config.json").read_text())["base_path"]).strip("/")
BASE = BASE.rstrip("/") + "/"
ORIGIN = os.environ.get("SITE_ORIGIN", json.loads((ROOT / "site.config.json").read_text())["origin"]).rstrip("/")


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.refs = []
        self.ids = set()
        self.base_url = ""
        self.html = {}
        self.canonical = None
        self.alternates = {}
        self.feed(path.read_text())

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "html":
            self.html = attrs
        if tag == "base":
            self.base_url = attrs.get("href", "")
        if tag == "link" and attrs.get("rel") == "canonical":
            self.canonical = attrs.get("href")
        if tag == "link" and attrs.get("rel") == "alternate":
            self.alternates[attrs.get("hreflang")] = attrs.get("href")
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag in ("a", "link") and attrs.get("href"):
            self.refs.append(attrs["href"])
        if tag == "form" and attrs.get("action"):
            self.refs.append(attrs["action"])
        if tag == "source" and attrs.get("srcset"):
            self.refs.extend(item.strip().split()[0] for item in attrs["srcset"].split(","))
        if tag in ("script", "img", "source") and attrs.get("src"):
            self.refs.append(attrs["src"])


pages = {p: Page(p) for p in DIST.rglob("*.html")}
errors = []
references = 0
for path, page in pages.items():
    current = "https://local.invalid" + BASE + path.relative_to(DIST).as_posix()
    current = urljoin(current, page.base_url)
    for raw in page.refs:
        url = urlsplit(urljoin(current, raw))
        if url.netloc != "local.invalid" or url.scheme not in ("http", "https"):
            continue
        if not url.path.startswith(BASE):
            errors.append(f"{path.relative_to(DIST)}: URL escapes site base: {raw}")
            continue
        target = DIST / unquote(url.path[len(BASE):])
        if url.path.endswith("/") or target.is_dir():
            target /= "index.html"
        references += 1
        if not target.is_file():
            errors.append(f"{path.relative_to(DIST)}: missing {raw}")
        elif url.fragment and target in pages and unquote(url.fragment) not in pages[target].ids:
            errors.append(f"{path.relative_to(DIST)}: missing fragment {raw}")

# Verify the actual static output crawlers receive, including the no-JS docs entry.
for path, page in pages.items():
    relative = path.relative_to(DIST).as_posix()
    if "data-site-base" not in page.html:
        continue
    language = "zh" if relative.startswith(("zh/", "docs/zh/")) else "en"
    if relative.startswith("docs/"):
        suffix = relative.split("/", 2)[-1] if relative != "docs/index.html" else "index.html"
        suffix = "" if suffix == "index.html" else suffix
        localized = {lang: BASE + f"docs/{lang}/" + suffix for lang in ("en", "zh")}
        default = BASE + "docs/" if not suffix else localized["en"]
    else:
        localized = {"en": BASE, "zh": BASE + "zh/"}
        default = BASE
    expected_alternates = {"en": ORIGIN + localized["en"], "zh-CN": ORIGIN + localized["zh"], "x-default": ORIGIN + default}
    if page.html.get("lang") != ("zh-CN" if language == "zh" else "en") or page.html["data-site-base"] != BASE:
        errors.append(f"{relative}: wrong static language or base path")
    if page.canonical != ORIGIN + localized[language] or page.alternates != expected_alternates:
        errors.append(f"{relative}: incorrect canonical or language alternates")
    expected_entry = {"index.html": "home", "docs/index.html": "docs"}.get(relative)
    if page.html.get("data-language-entry") != expected_entry:
        errors.append(f"{relative}: only neutral entries may auto-select a language")
    if not any(ref.startswith(BASE + "assets/language.js?") for ref in page.refs):
        errors.append(f"{relative}: missing language preference script")
for relative, english_text in (("index.html", "Different rhythms."), ("docs/index.html", "A2RT documentation")):
    if english_text not in (DIST / relative).read_text():
        errors.append(f"{relative}: static English content missing")
if pages[DIST / "docs/index.html"].base_url != BASE + "docs/en/":
    errors.append("Default docs entry must resolve relative resources against English docs")

credential = re.compile(r"(?:sk-[A-Za-z0-9_-]{16,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")
for path in DIST.rglob("*"):
    if path.is_file() and path.suffix in (".html", ".js", ".json", ".txt", ".md"):
        body = path.read_text(errors="ignore")
        if credential.search(body):
            errors.append(f"Potential credential in {path.relative_to(DIST)} (value not printed)")
        if "<built-in method" in body:
            errors.append(f"Template interpolation error in {path.relative_to(DIST)}")

source_info = json.loads((ROOT / "protocol/SOURCE.json").read_text())
index_root = DIST / "docs/ai-index"
version = json.loads((index_root / "version.json").read_text())
for field in ("status", "revision", "wire_protocol_version", "source_commit"):
    if version.get(field) != source_info[field]:
        errors.append(f"Search index provenance mismatch: {field}")
for artifact in index_root.glob("*.json"):
    if artifact.read_bytes() != (ROOT / "worker/assets/index" / artifact.name).read_bytes():
        errors.append(f"Public and Worker indexes differ: {artifact.name}")

expected_specs = {f"spec/{path.stem}.html" for path in (ROOT / "protocol").glob("0[1-4]-*.md")}
expected_profiles = {"profiles/canvas.html", *{f"profiles/canvas-realtime/{page}.html" for page in ("index", "interaction", "binary-binding")}}
for name in ("zh", "en"):
    chunks = json.loads((DIST / f"docs/ai-index/chunks_{name}.json").read_text())
    if not chunks or any(len(item.get("embedding", [])) != 384 for item in chunks):
        errors.append(f"Invalid {name} search index")
    indexed = {item["source_path"] for item in chunks}
    if {path for path in indexed if path.startswith("spec/")} != expected_specs or not expected_profiles <= indexed:
        errors.append(f"{name} index does not match the current architecture chapters")
    for chunk in chunks:
        citation = urlsplit(chunk["docs_url"])
        target = DIST / "docs" / unquote(citation.path.lstrip("/"))
        if target not in pages or (citation.fragment and unquote(citation.fragment) not in pages[target].ids):
            errors.append(f"Invalid {name} search citation: {chunk['docs_url']}")
if errors:
    raise SystemExit("\n".join(errors))
print(f"Passed: {len(pages)} HTML pages, {references} local references, bilingual indexes, and public artifact credential scan.")
