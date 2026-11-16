"""Build the landing pages, Sphinx docs, public fixtures, and Worker index."""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import posixpath
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from urllib.parse import urlparse

from site_ui import shell_context

from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parent.parent


def run(*args, env=None):
    subprocess.run(args, cwd=ROOT, env=env, check=True)


def config():
    result = json.loads((ROOT / "site.config.json").read_text())
    result["origin"] = os.environ.get("SITE_ORIGIN", result["origin"]).rstrip("/")
    result["base_path"] = "/" + os.environ.get("SITE_BASE_PATH", result["base_path"]).strip("/")
    result["base_path"] = result["base_path"].rstrip("/") + "/"
    for field, variable in [("ai_endpoint", "DOCS_AI_ENDPOINT"), ("turnstile_site_key", "TURNSTILE_SITE_KEY")]:
        # Unset GitHub Actions Variables are passed as empty strings. Preserve
        # the checked-in public defaults unless a nonempty override is supplied.
        result[field] = os.environ.get(variable, "").strip() or result[field].strip()
    for field in ("origin", "ai_endpoint"):
        value = result[field]
        if value and (urlparse(value).scheme != "https" or not urlparse(value).netloc or urlparse(value).username):
            raise ValueError(f"{field} must be an HTTPS URL without embedded credentials")
    if result["ai_endpoint"] and not result["turnstile_site_key"]:
        raise ValueError("Set TURNSTILE_SITE_KEY together with DOCS_AI_ENDPOINT")
    return result


def prepare_docs(cfg):
    source = ROOT / "build/docs-source"
    if source.exists():
        shutil.rmtree(source)
    shutil.copytree(ROOT / "docs/source", source, dirs_exist_ok=True)
    for page in source.rglob("*.md"):
        page.write_text(page.read_text().replace("{{ base }}", cfg["base_path"]))
    # Keep the overview, Core chapters, and current Profiles tied to one snapshot.
    pages = {"README.md": "overview.md", "profiles/canvas/README.md": "profiles/canvas.md"}
    pages.update({p.name: f"spec/{p.name}" for p in (ROOT / "protocol").glob("0[1-4]-*.md")})
    pages.update({f"profiles/canvas-realtime/{name}": f"profiles/canvas-realtime/{target}" for name, target in (
        ("README.md", "index.md"), ("01-interaction-and-delivery.md", "interaction.md"),
        ("02-binary-binding.md", "binary-binding.md"))})
    for original, destination in pages.items():
        def source_link(match):
            label, href = match.groups()
            if urlparse(href).scheme or href.startswith(("#", "/")):
                return match[0]
            path, separator, fragment = href.partition("#")
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(original), path))
            if resolved in pages:
                target = posixpath.relpath(pages[resolved], posixpath.dirname(destination) or ".")
            else:
                if not (ROOT / "protocol" / resolved).is_file():
                    raise ValueError(f"Missing protocol link: {original}: {href}")
                target = cfg["base_path"] + "protocol/" + resolved
            return f"[{label}]({target}{separator}{fragment})"

        body = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", source_link, (ROOT / "protocol" / original).read_text())
        if original == "README.md":
            body = re.sub(r"^# .*", "# 协议概览", body, count=1)
        if original == "profiles/canvas-realtime/README.md":
            body += "\n```{toctree}\n:maxdepth: 1\n\ninteraction\nbinary-binding\n```\n"
        # CommonMark needs separation after punctuation-ending emphasis before
        # adjacent CJK prose. Adapt rendering without modifying the source copy.
        body = re.sub(r"([）”])\*\*(?=[\u4e00-\u9fff])", r"\1** ", body)
        # Render the source's small architecture diagram without a JS/CDN dependency.
        body = re.sub(r"```mermaid\n.*?```", f'<img src="{cfg["base_path"]}assets/clock-groups.svg" alt="根时钟、子时钟、独立同步组及其轨道">', body, flags=re.S)
        target = source / "zh" / destination
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body)
    for page in source.rglob("*.md"):
        body = re.sub(r"\[([^\]]+)\]\((/[^)]+)\)", lambda m: '<a href="' + html.escape(m[2], quote=True) + '">' + html.escape(m[1]) + '</a>', page.read_text())
        body = re.sub(r'<img src="[^"]*/assets/clock-groups.svg"([^>]*)>',
                      lambda match: f'<picture><source media="(max-width: 600px)" srcset="{cfg["base_path"]}assets/clock-groups-mobile.svg"><img src="{cfg["base_path"]}assets/clock-groups.svg" width="840" height="430"{match[1]}></picture>', body)
        page.write_text(body)
    return source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--home-only", action="store_true", help="Quick landing-page preview; docs are built by the full command")
    parser.add_argument("--preview", action="store_true", help="Use local search without calling the production AI Worker")
    args = parser.parse_args()
    cfg = config()
    if args.preview:
        cfg.update(ai_endpoint="", turnstile_site_key="")
    out = ROOT / "dist"
    if not args.home_only and out.exists():
        shutil.rmtree(out)
    out.mkdir(exist_ok=True)
    shutil.copytree(ROOT / "site/assets", out / "assets", dirs_exist_ok=True)
    shutil.copytree(ROOT / "protocol", out / "protocol", dirs_exist_ok=True, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (out / ".nojekyll").write_text("")
    hostname = urlparse(cfg["origin"]).hostname
    if not hostname.endswith(".github.io"):
        (out / "CNAME").write_text(hostname + "\n")

    content = json.loads((ROOT / "site/content.json").read_text())
    chapter = (ROOT / "protocol/01-clock-sync-group-track-model.md").read_text()
    illustration = json.loads(re.search(r"```json\s*\n(.*?)\n```", chapter, re.S)[1])
    (out / "assets/architecture-example.json").write_text(json.dumps(illustration, indent=2, ensure_ascii=False) + "\n")
    examples = {
        "clocks": illustration["clocks"][:2],
        "group": illustration["sync_groups"][0],
        "track": illustration["tracks"][0],
    }
    jinja = Environment(loader=FileSystemLoader(ROOT / "site"), autoescape=select_autoescape(["html"]))
    # Refresh cached styles and icons whenever their content changes.
    asset_hash = hashlib.sha256()
    asset_hash.update(json.dumps(illustration, sort_keys=True).encode())
    for asset in sorted((ROOT / "site/assets").rglob("*")):
        if asset.is_file():
            asset_hash.update(asset.relative_to(ROOT / "site/assets").as_posix().encode())
            asset_hash.update(asset.read_bytes())
    jinja.globals["asset_version"] = asset_hash.hexdigest()[:12]
    for lang, t in content.items():
        home = cfg["base_path"] + ("en/" if lang == "en" else "")
        client = {"groups": t["groups"], "examples": examples, **{key: t[key] for key in ("copy", "copied", "copy_failed", "play_motion", "pause_motion", "tracks_label", "track_label")}}
        rendered = jinja.get_template("home.html").render(
            **shell_context(cfg, lang),
            t=t, lang=lang, home=home, origin=cfg["origin"], base=cfg["base_path"],
            canonical=cfg["origin"] + home, alternate=cfg["base_path"] + ("en/" if lang == "zh" else ""),
            docs=cfg["base_path"] + f"docs/{lang}/", repo=cfg["repository"], year=datetime.now(timezone.utc).year,
            initial_example=json.dumps(examples["clocks"], indent=2, ensure_ascii=False),
            client_data=json.dumps(client, ensure_ascii=False).replace("<", "\\u003c"),
        )
        target = out / ("en/index.html" if lang == "en" else "index.html")
        target.parent.mkdir(exist_ok=True)
        target.write_text(rendered)
    (out / "404.html").write_text(jinja.get_template("404.html").render(base=cfg["base_path"]))
    (out / "brand").mkdir(exist_ok=True)
    (out / "brand/index.html").write_text(jinja.get_template("brand.html").render(base=cfg["base_path"]))
    if args.home_only:
        print("Landing pages built in dist/")
        return

    source = prepare_docs(cfg)
    env = dict(os.environ, A2RT_SITE_CONFIG=json.dumps(cfg))
    for lang in ("zh", "en"):
        run(sys.executable, "-m", "sphinx", "-W", "--keep-going", "-b", "html", "-c", str(ROOT / "docs"),
            str(source / lang), str(out / "docs" / lang), env=dict(env, DOCS_LANGUAGE=lang))
    (out / "docs/index.html").write_text(jinja.get_template("docs-index.html").render(base=cfg["base_path"]))
    # Index only the built docs, not the landing page or deployment secrets.
    run(sys.executable, "scripts/build_index.py", "--html-dir", str(out / "docs"), "--output-dir", str(ROOT / "build/ai/index"))
    asset_dir = ROOT / "worker/assets/index"
    if asset_dir.exists():
        shutil.rmtree(asset_dir)
    shutil.copytree(ROOT / "build/ai/index", asset_dir)
    source_info = json.loads((ROOT / "protocol/SOURCE.json").read_text())
    version = {key: source_info[key] for key in ("status", "revision", "wire_protocol_version", "source_commit")}
    version["commit"] = os.environ.get("GITHUB_SHA") or subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    for location in (ROOT / "build/ai/index/version.json", asset_dir / "version.json"):
        location.write_text(json.dumps(version, ensure_ascii=False, indent=2) + "\n")
    # Publish the exact same documentation index with Pages for inspection.
    shutil.copytree(ROOT / "build/ai/index", out / "docs/ai-index", dirs_exist_ok=True)
    urls = [cfg["origin"] + cfg["base_path"] + str(path.relative_to(out)).replace("index.html", "")
            for path in out.rglob("*.html") if path.name not in ("404.html", "search.html", "genindex.html")]
    (out / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(f"<url><loc>{url}</loc></url>" for url in sorted(urls)) + "</urlset>\n")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {cfg['origin']}{cfg['base_path']}sitemap.xml\n")
    print(f"Built website + bilingual docs in {out}; Worker index in {asset_dir}")


if __name__ == "__main__":
    main()
