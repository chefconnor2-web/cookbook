#!/usr/bin/env python3
"""Build Amazon KDP print-ready PDFs for the cookbook.

    python3 build.py

Reads book.yaml and the recipe markdown files, and writes:
    build/interior.pdf   -- the inside pages (upload as "Manuscript")
    build/cover.pdf      -- the full wraparound cover (upload as "Book Cover")
"""
import html
import re
import sys
from pathlib import Path

import markdown
import yaml
from PIL import Image
from weasyprint import HTML

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"

# --- Amazon KDP paperback rules -------------------------------------------
BLEED = 0.125                      # inches, cover (and full-bleed interiors)
OUTSIDE_MARGIN = 0.5               # KDP minimum is 0.25"; 0.5" looks better
TOP_BOTTOM_MARGIN = 0.75
MIN_PAGES, MAX_PAGES = 24, 828
SPINE_TEXT_MIN_PAGES = 80          # KDP allows spine text only above 79 pages
PAGE_THICKNESS = {                 # inches per page
    ("white", "bw"): 0.002252,
    ("cream", "bw"): 0.0025,
    ("white", "standard-color"): 0.002252,
    ("white", "premium-color"): 0.002347,
}
GUTTER_BY_PAGES = [(150, 0.375), (300, 0.5), (500, 0.625), (700, 0.75), (828, 0.875)]
MIN_DPI = 300


def gutter_for(pages):
    for limit, gutter in GUTTER_BY_PAGES:
        if pages <= limit:
            return gutter
    sys.exit(f"Error: {pages} pages is over KDP's {MAX_PAGES}-page limit.")


def esc(text):
    return html.escape(str(text or ""))


def md(text):
    return markdown.markdown(text or "", extensions=["extra", "smarty"])


def load_recipe(path):
    raw = (ROOT / path).read_text(encoding="utf-8")
    meta, body = {}, raw
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if m:
        meta, body = yaml.safe_load(m.group(1)) or {}, m.group(2)
    meta.setdefault("title", Path(path).stem.replace("-", " ").title())
    return meta, body


def check_image(path, print_width_in, warnings):
    full = ROOT / path
    if not full.exists():
        sys.exit(f"Error: image not found: {path}")
    with Image.open(full) as im:
        dpi = im.width / print_width_in
    if dpi < MIN_DPI:
        warnings.append(f"{path} is only ~{dpi:.0f} dpi at print size "
                        f"(KDP wants {MIN_DPI}); it may print blurry.")
    return full.as_uri()


def slug(text, n):
    return f"r{n}-" + re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


# --- Interior ---------------------------------------------------------------

def interior_css(w, h, gutter):
    font = (ROOT / "fonts").as_uri()
    return f"""
@font-face {{ font-family: Lora; src: url({font}/Lora-Regular.ttf); }}
@font-face {{ font-family: Lora; font-weight: bold; src: url({font}/Lora-Bold.ttf); }}
@font-face {{ font-family: Lora; font-style: italic; src: url({font}/Lora-Italic.ttf); }}
@font-face {{ font-family: Lora; font-weight: bold; font-style: italic;
              src: url({font}/Lora-BoldItalic.ttf); }}

@page {{
  size: {w}in {h}in;
  margin: {TOP_BOTTOM_MARGIN}in {OUTSIDE_MARGIN}in;
  @bottom-center {{ content: counter(page); font: 9pt Lora; color: #555; }}
}}
@page :left  {{ margin-left: {OUTSIDE_MARGIN}in; margin-right: {gutter}in;
  @top-left {{ content: string(chapter); font: italic 9pt Lora; color: #555; }} }}
@page :right {{ margin-left: {gutter}in; margin-right: {OUTSIDE_MARGIN}in;
  @top-right {{ content: string(recipe); font: italic 9pt Lora; color: #555; }} }}
@page front {{ @bottom-center {{ content: none; }} @top-left {{ content: none; }}
               @top-right {{ content: none; }} }}
@page opener {{ @top-left {{ content: none; }} @top-right {{ content: none; }} }}
@page :blank {{ @bottom-center {{ content: none; }} @top-left {{ content: none; }}
                @top-right {{ content: none; }} }}

html {{ font-family: Lora, serif; font-size: 10.5pt; line-height: 1.5; color: #111; }}
h1, h2, h3 {{ font-weight: bold; line-height: 1.2; }}
img {{ max-width: 100%; }}

.front {{ page: front; break-before: page; }}
.title-page {{ text-align: center; padding-top: 30%; }}
.title-page h1 {{ font-size: 32pt; margin: 0; }}
.title-page .subtitle {{ font-style: italic; font-size: 14pt; margin-top: .5em; }}
.title-page .author {{ font-size: 14pt; margin-top: 4em; letter-spacing: .1em;
                       text-transform: uppercase; }}
.copyright {{ font-size: 8.5pt; padding-top: 70%; }}
.dedication {{ text-align: center; font-style: italic; padding-top: 35%; }}
.toc h2, .intro h2 {{ font-size: 20pt; margin-top: 0; }}
.toc ul {{ list-style: none; padding: 0; }}
.toc li.toc-chapter {{ font-weight: bold; margin-top: .9em; }}
.toc li.toc-recipe {{ margin-left: 1.2em; }}
.toc a {{ color: inherit; text-decoration: none; }}
.toc a::after {{ content: target-counter(attr(href), page); float: right; }}
.intro {{ break-before: right; }}

.chapter-opener {{ page: opener; break-before: right; text-align: center;
                   padding-top: 35%; string-set: chapter content(text); }}
.chapter-opener h1 {{ font-size: 30pt; margin: 0; string-set: chapter content(); }}
.chapter-opener .chapter-intro {{ font-style: italic; margin-top: 1em; }}

.recipe {{ break-before: page; }}
.recipe h1 {{ font-size: 22pt; margin: 0 0 .3em; string-set: recipe content(); }}
.recipe .lede {{ font-style: italic; }}
.recipe .meta {{ font-size: 9pt; letter-spacing: .08em; text-transform: uppercase;
                 border-top: .5pt solid #999; border-bottom: .5pt solid #999;
                 padding: .35em 0; margin: 1em 0; }}
.recipe .photo {{ margin: 0 0 1em; }}
.recipe h2 {{ font-size: 12pt; text-transform: uppercase; letter-spacing: .1em;
              margin: 1.2em 0 .5em; break-after: avoid; }}
.recipe .ingredients ul {{ columns: 2; column-gap: 2em; padding-left: 1.1em; margin: 0; }}
.recipe .ingredients li {{ break-inside: avoid; }}
.recipe ol li {{ margin-bottom: .5em; break-inside: avoid; }}
.blank {{ break-before: page; page: front; }}
"""


def render_recipe(path, n, text_width, warnings):
    meta, body = load_recipe(path)
    title = meta["title"]
    meta_bits = [f"{k.title()} {esc(meta[k])}" for k in ("serves", "prep", "cook") if meta.get(k)]
    photo = ""
    if meta.get("image"):
        photo = f'<div class="photo"><img src="{check_image(meta["image"], text_width, warnings)}"></div>'

    # Wrap the "Ingredients" section so it can flow into two columns.
    body_html = md(body)
    body_html = re.sub(r"(<h2>Ingredients</h2>\s*)(<ul>.*?</ul>)",
                       r'\1<div class="ingredients">\2</div>', body_html, flags=re.S | re.I)
    return title, f"""
<section class="recipe" id="{slug(title, n)}">
  <h1>{esc(title)}</h1>
  {f'<div class="lede">{md(meta.get("intro"))}</div>' if meta.get("intro") else ""}
  {f'<div class="meta">{" &nbsp;·&nbsp; ".join(meta_bits)}</div>' if meta_bits else ""}
  {photo}
  {body_html}
</section>"""


def interior_html(cfg, w, h, gutter, blank_pages, warnings):
    text_width = w - gutter - OUTSIDE_MARGIN
    parts, toc = [], []

    year = esc(cfg.get("year", ""))
    isbn = f"<p>ISBN {esc(cfg['isbn'])}</p>" if cfg.get("isbn") else ""
    publisher = f"<p>Published by {esc(cfg['publisher'])}</p>" if cfg.get("publisher") else ""
    parts.append(f"""
<section class="front title-page">
  <h1>{esc(cfg['title'])}</h1>
  {f'<div class="subtitle">{esc(cfg["subtitle"])}</div>' if cfg.get("subtitle") else ""}
  <div class="author">{esc(cfg['author'])}</div>
</section>
<section class="front copyright">
  <p>Copyright © {year} {esc(cfg['author'])}. All rights reserved.</p>
  <p>No part of this book may be reproduced in any form without written
     permission from the author, except for brief quotations in reviews.</p>
  {publisher}{isbn}
</section>""")

    if cfg.get("dedication"):
        parts.append(f'<section class="front dedication">'
                     f'{md((ROOT / cfg["dedication"]).read_text(encoding="utf-8"))}</section>')

    n = 0
    body = []
    for ci, chapter in enumerate(cfg.get("chapters") or []):
        cid = f"ch{ci}"
        toc.append(f'<li class="toc-chapter"><a href="#{cid}">{esc(chapter["title"])}</a></li>')
        body.append(f"""
<section class="chapter-opener" id="{cid}">
  <h1>{esc(chapter['title'])}</h1>
  {f'<div class="chapter-intro">{md(chapter.get("intro"))}</div>' if chapter.get("intro") else ""}
</section>""")
        for path in chapter.get("recipes") or []:
            n += 1
            title, section = render_recipe(path, n, text_width, warnings)
            toc.append(f'<li class="toc-recipe"><a href="#{slug(title, n)}">{esc(title)}</a></li>')
            body.append(section)

    parts.append(f'<section class="front toc"><h2>Contents</h2><ul>{"".join(toc)}</ul></section>')
    if cfg.get("introduction"):
        parts.append(f'<section class="intro"><h2>Introduction</h2>'
                     f'{md((ROOT / cfg["introduction"]).read_text(encoding="utf-8"))}</section>')
    parts.extend(body)
    parts.append('<div class="blank"></div>' * blank_pages)

    return f"""<!doctype html><html><head><meta charset="utf-8">
<title>{esc(cfg['title'])}</title><style>{interior_css(w, h, gutter)}</style></head>
<body>{''.join(parts)}</body></html>"""


def build_interior(cfg, w, h):
    """Render, re-rendering until the gutter matches the final page count."""
    gutter, blanks = GUTTER_BY_PAGES[0][1], 0
    for _ in range(10):
        warnings = []
        doc = HTML(string=interior_html(cfg, w, h, gutter, blanks, warnings),
                   base_url=str(ROOT)).render()
        pages = len(doc.pages)
        # Pad short books up to KDP's minimum, and to an even page count.
        target = max(MIN_PAGES, pages + (pages % 2))
        if target != pages:
            blanks += target - pages
            continue
        if gutter_for(pages) != gutter:
            gutter = gutter_for(pages)
            continue
        doc.write_pdf(BUILD / "interior.pdf")
        return pages, gutter, blanks, warnings
    sys.exit("Error: page layout did not settle; please report this.")


# --- Cover ------------------------------------------------------------------

def build_cover(cfg, w, h, pages, warnings):
    key = (cfg.get("paper", "white"), cfg.get("ink", "bw"))
    if key not in PAGE_THICKNESS:
        sys.exit(f"Error: KDP doesn't offer paper={key[0]} with ink={key[1]}.")
    spine = pages * PAGE_THICKNESS[key]
    cw, ch = BLEED + w + spine + w + BLEED, BLEED + h + BLEED
    c = cfg.get("cover") or {}
    bg, fg = c.get("background", "#2f3b2f"), c.get("text_color", "#f4efe6")
    font = (ROOT / "fonts").as_uri()

    front_img = ""
    if c.get("front_image"):
        uri = check_image(c["front_image"], w + BLEED, warnings)
        front_img = f'<img class="front-img" src="{uri}">'

    spine_text = ""
    if pages >= SPINE_TEXT_MIN_PAGES:
        spine_text = (f'<div class="spine-text">{esc(cfg["title"])}'
                      f' &nbsp;·&nbsp; {esc(cfg["author"])}</div>')

    front_left = BLEED + w + spine
    html_doc = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: Lora; src: url({font}/Lora-Regular.ttf); }}
@font-face {{ font-family: Lora; font-weight: bold; src: url({font}/Lora-Bold.ttf); }}
@font-face {{ font-family: Lora; font-style: italic; src: url({font}/Lora-Italic.ttf); }}
@page {{ size: {cw}in {ch}in; margin: 0; }}
html, body {{ margin: 0; font-family: Lora, serif; color: {fg}; }}
.cover {{ position: relative; width: {cw}in; height: {ch}in; background: {bg}; overflow: hidden; }}
.front-img {{ position: absolute; left: {front_left}in; top: 0;
              width: {w + BLEED}in; height: {ch}in; object-fit: cover; }}
/* Keep text 0.25in inside the trim line on every side (KDP safe zone). */
.front {{ position: absolute; left: {front_left + 0.375}in; top: {BLEED + 1.2}in;
          width: {w - 0.75}in; text-align: center; }}
.front h1 {{ font-size: 40pt; margin: 0; line-height: 1.1; }}
.front .subtitle {{ font-style: italic; font-size: 15pt; margin-top: .6em; }}
.front-author {{ position: absolute; left: {front_left + 0.375}in; width: {w - 0.75}in;
                  top: {BLEED + h - 1.4}in; text-align: center; font-size: 16pt;
                  letter-spacing: .12em; text-transform: uppercase; }}
.back {{ position: absolute; left: {BLEED + 0.5}in; top: {BLEED + 1}in;
         width: {w - 1}in; font-size: 11pt; line-height: 1.55; }}
/* KDP prints the barcode here: keep this area clear. */
.spine-text {{ position: absolute; left: {BLEED + w + spine / 2}in; top: {ch / 2}in;
               width: {h - 1}in; transform: translate(-50%, -50%) rotate(90deg);
               text-align: center; font-size: {min(12, spine * 72 * 0.55):.1f}pt;
               white-space: nowrap; }}
</style></head><body><div class="cover">
  {front_img}
  <div class="back">{md(c.get("back_text"))}</div>
  {spine_text}
  <div class="front"><h1>{esc(cfg['title'])}</h1>
    {f'<div class="subtitle">{esc(cfg["subtitle"])}</div>' if cfg.get("subtitle") else ""}</div>
  <div class="front-author">{esc(cfg['author'])}</div>
</div></body></html>"""
    HTML(string=html_doc, base_url=str(ROOT)).write_pdf(BUILD / "cover.pdf")
    return spine, cw, ch


def main():
    cfg = yaml.safe_load((ROOT / "book.yaml").read_text(encoding="utf-8"))
    try:
        w, h = (float(x) for x in str(cfg.get("trim", "8x10")).lower().split("x"))
    except ValueError:
        sys.exit('Error: trim should look like "8x10".')
    BUILD.mkdir(exist_ok=True)

    pages, gutter, blanks, warnings = build_interior(cfg, w, h)
    spine, cw, ch = build_cover(cfg, w, h, pages, warnings)

    print(f"""
Built for Amazon KDP paperback ({w:g} x {h:g} in, {cfg.get('paper', 'white')} paper, {cfg.get('ink', 'bw')} ink)
  build/interior.pdf  {pages} pages, inside margin {gutter} in{f', {blanks} blank pages added at the end' if blanks else ''}
  build/cover.pdf     {cw:.3f} x {ch:.3f} in, spine {spine:.3f} in{'' if pages >= SPINE_TEXT_MIN_PAGES else ' (too thin for spine text)'}

On KDP choose: trim {w:g} x {h:g} in, "No bleed", matte or glossy cover,
and upload interior.pdf as the manuscript and cover.pdf as the cover.""")
    for msg in warnings:
        print(f"WARNING: {msg}")


if __name__ == "__main__":
    main()
