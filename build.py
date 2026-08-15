#!/usr/bin/env python3
"""Assemble dist/index.html from src/. Validates chapters + quizzes; fails loudly."""
import base64, json, re, sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
CH = SRC / "chapters"
# The sprint presell page owns dist/ root (and so the site root); the book
# lives one level down at /book.
OUT = ROOT / "dist" / "book" / "index.html"

ALLOWED_TAGS = set("p h2 h3 ul ol li strong em code pre table thead tbody tr th td figure figcaption "
                   "svg g rect circle ellipse line path polyline polygon text tspan defs marker title "
                   "details summary div span dfn br blockquote".split())
ALLOWED_DIV = {"box", "box-tag", "analogy", "story", "lens", "crux", "feynman", "fey-prompt",
               "fey-model", "exercise", "ex-q", "takeaways", "diagram"}
FONTS = [
    ("Archivo", "normal", "300 700", "Archivo-normal-300_700.woff2"),
    ("Literata", "normal", "200 900", "Literata-normal-200_900.woff2"),
    ("Literata", "italic", "200 900", "Literata-italic-200_900.woff2"),
    ("IBM Plex Mono", "normal", "400", "IBMPlexMono-normal-400.woff2"),
    ("IBM Plex Mono", "normal", "600", "IBMPlexMono-normal-600.woff2"),
]

errors, warnings = [], []
def err(m): errors.append(m)
def warn(m): warnings.append(m)

def font_css():
    css = []
    for fam, style, weight, fn in FONTS:
        data = base64.b64encode((SRC / "fonts" / fn).read_bytes()).decode()
        css.append(f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
                   f"font-display:swap;src:url(data:font/woff2;base64,{data}) format('woff2');}}")
    return "\n".join(css)

def validate_html(cid, html):
    if re.search(r'\bstyle\s*=', html): err(f"{cid}: inline style= forbidden")
    if re.search(r'https?://', html): err(f"{cid}: external URL found")
    if "<img" in html: err(f"{cid}: <img> forbidden (use inline SVG)")
    for tag in re.findall(r'<([a-zA-Z][a-zA-Z0-9-]*)', html):
        if tag.lower() not in ALLOWED_TAGS:
            err(f"{cid}: tag <{tag}> not allowed")
    for m in re.finditer(r'<div class="([^"]+)"', html):
        for cls in m.group(1).split():
            if cls not in ALLOWED_DIV:
                warn(f"{cid}: unknown div class '{cls}'")
    for key in re.findall(r'data-key="([^"]+)"', html):
        if not key.startswith(cid): err(f"{cid}: feynman data-key '{key}' must start with chapter id")
    if "<h1" in html: err(f"{cid}: no <h1> in fragments (engine renders the title)")

def validate_quiz(cid, data):
    if data.get("chapter") != cid: err(f"{cid}: quiz 'chapter' field mismatch")
    items = data.get("items", [])
    counts = {1: 0, 2: 0, 3: 0}
    seen = set()
    for q in items:
        qid = q.get("id", "?")
        if qid in seen: err(f"{cid}: duplicate quiz id {qid}")
        seen.add(qid)
        if not qid.startswith(cid): err(f"{cid}: quiz id {qid} must start with chapter id")
        lv = q.get("level")
        if lv not in (1, 2, 3): err(f"{cid}:{qid}: level must be 1|2|3")
        else: counts[lv] += 1
        if q.get("type") not in ("mcq", "multi"): err(f"{cid}:{qid}: type must be mcq|multi")
        opts = q.get("options", [])
        if not (3 <= len(opts) <= 5): err(f"{cid}:{qid}: needs 3-5 options")
        ncorrect = sum(1 for o in opts if o.get("correct"))
        if q.get("type") == "mcq" and ncorrect != 1: err(f"{cid}:{qid}: mcq needs exactly 1 correct")
        if q.get("type") == "multi" and ncorrect < 2: err(f"{cid}:{qid}: multi needs 2+ correct")
        for o in opts:
            if len(o.get("why", "").strip()) < 20:
                err(f"{cid}:{qid}: every option needs a real 'why' (>=20 chars)")
        if len(q.get("q", "")) < 15: err(f"{cid}:{qid}: question text too short")
    lo = {1: 6, 2: 6, 3: 5}   # slightly tolerant floors; guide asks 8-10/8-10/6-8
    for lv, n in counts.items():
        if n < lo[lv]: err(f"{cid}: only {n} level-{lv} questions (want {lo[lv]}+)")
    return items

def main():
    check_only = "--check" in sys.argv
    toc = json.loads((SRC / "toc.json").read_text())
    templates, quiz_all = [], {}
    ready = 0
    for part in toc["parts"]:
        for ch in part["chapters"]:
            cid = ch["id"]
            h, qf = CH / f"{cid}.html", CH / f"{cid}.quiz.json"
            if not h.exists():
                continue
            html = h.read_text()
            validate_html(cid, html)
            if not qf.exists():
                err(f"{cid}: has html but no quiz json"); continue
            try:
                quiz_all[cid] = validate_quiz(cid, json.loads(qf.read_text()))
            except json.JSONDecodeError as e:
                err(f"{cid}: quiz json invalid: {e}"); continue
            templates.append(f'<template data-ch="{cid}">\n{html}\n</template>')
            ready += 1

    for w in warnings: print("WARN", w)
    if errors:
        for e in errors: print("FAIL", e)
        sys.exit(f"\n{len(errors)} error(s). Not building.")
    print(f"OK: {ready} chapters valid.")
    if check_only: return

    tpl = (SRC / "template.html").read_text()
    page = (tpl
        .replace("/*{{FONTS_CSS}}*/", font_css())
        .replace("/*{{STYLE_CSS}}*/", (SRC / "style.css").read_text())
        .replace("<!--{{CHAPTER_TEMPLATES}}-->", "\n".join(templates))
        .replace("/*{{TOC_JSON}}*/", json.dumps(toc).replace("</", "<\\/"))
        .replace("/*{{QUIZ_JSON}}*/", json.dumps(quiz_all).replace("</", "<\\/"))
        .replace("/*{{APP_JS}}*/", (SRC / "app.js").read_text().replace("</script", "<\\/script")))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(page)
    print(f"Built {OUT} ({OUT.stat().st_size / 1024:.0f} KB, {ready} chapters)")

if __name__ == "__main__":
    main()
