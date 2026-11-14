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


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.refs = []
        self.ids = set()
        self.feed(path.read_text())

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if attrs.get("id"):
            self.ids.add(attrs["id"])
        if tag in ("a", "link") and attrs.get("href"):
            self.refs.append(attrs["href"])
        if tag in ("script", "img", "source") and attrs.get("src"):
            self.refs.append(attrs["src"])


pages = {p: Page(p) for p in DIST.rglob("*.html")}
errors = []
references = 0
for path, page in pages.items():
    current = "https://local.invalid" + BASE + path.relative_to(DIST).as_posix()
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

credential = re.compile(r"(?:sk-[A-Za-z0-9_-]{16,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")
for path in DIST.rglob("*"):
    if path.is_file() and path.suffix in (".html", ".js", ".json", ".txt", ".md"):
        body = path.read_text(errors="ignore")
        if credential.search(body):
            errors.append(f"Potential credential in {path.relative_to(DIST)} (value not printed)")
        if "<built-in method" in body:
            errors.append(f"Template interpolation error in {path.relative_to(DIST)}")

for name in ("zh", "en"):
    chunks = json.loads((DIST / f"docs/ai-index/chunks_{name}.json").read_text())
    if not chunks or any(len(item.get("embedding", [])) != 384 for item in chunks):
        errors.append(f"Invalid {name} search index")
if errors:
    raise SystemExit("\n".join(errors))
print(f"Passed: {len(pages)} HTML pages, {references} local references, bilingual indexes, and public artifact credential scan.")
