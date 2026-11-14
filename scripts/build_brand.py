"""Generate A2RT's editable, font-independent SVG identity from one geometry."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "site/assets"
GREEN = "#b6f36a"
INK = "#142019"

# Two folded bands form an open A. The detached point is a live signal.
SYMBOL = '''<path d="M8 76 33 20C36 13 44 13 47 20L57 43H43L40 36 22 76Z"/>
  <path d="M30 50H60L72 76H58L52 63H24Z"/>
  <circle cx="83" cy="69" r="7"/>'''

# Custom outlined letters, with no external font dependency.
LETTERS = '''<path fill-rule="evenodd" d="M112 68 127 28H139L154 68H143L140 59H126L123 68ZM129 50H137L133 38Z"/>
  <path d="M162 40C162 31 170 27 181 27 192 27 199 32 199 40 199 47 195 51 188 55L179 59H200V68H161V61L182 48C187 45 189 43 189 41 189 38 186 36 181 36 176 36 173 38 173 41H162Z"/>
  <path fill-rule="evenodd" d="M210 68V28H230C242 28 249 33 249 42 249 48 246 52 241 54L251 68H238L229 56H220V68ZM220 37V47H229C236 47 239 45 239 42S236 37 229 37Z"/>
  <path d="M257 28H296V38H282V68H271V38H257Z"/>'''


def svg(viewbox, body, label):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="{viewbox}" role="img" aria-labelledby="title">
<title id="title">{label}</title>
{body}
</svg>\n'''


def main():
    ASSETS.mkdir(parents=True, exist_ok=True)
    for suffix, mark, text in [("", GREEN, "#eef2ef"), ("-dark", INK, INK)]:
        (ASSETS / f"mark{suffix}.svg").write_text(svg("0 0 96 96", f'<g fill="{mark}">{SYMBOL}</g>', "A2RT signal mark"))
        (ASSETS / f"logo{suffix}.svg").write_text(svg("0 0 304 96", f'<g fill="{mark}">{SYMBOL}</g>\n<g fill="{text}">{LETTERS}</g>', "A2RT"))
    favicon = svg("0 0 96 96", f'<rect width="96" height="96" rx="23" fill="{GREEN}"/>\n<g transform="translate(4 3) scale(.91)" fill="{INK}">{SYMBOL}</g>', "A2RT")
    (ASSETS / "favicon.svg").write_text(favicon)
    for name in ("mark.svg", "logo.svg", "favicon.svg"):
        (ROOT / "docs/static" / name).write_text((ASSETS / name).read_text())
    print("Generated A2RT SVG marks, wordmarks, and favicon.")


if __name__ == "__main__":
    main()
