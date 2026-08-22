#!/usr/bin/env python3
"""Assemble dist/book/ and dist/origins/ from src/. Validates chapters + quizzes; fails loudly."""
import base64, json, re, sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
CH = SRC / "chapters"
# The sprint presell page owns dist/ root (and so the site root); the book
# lives one level down at /book, and its story-first twin at /origins.
DIST = ROOT / "dist"
SITE = "https://hld-gym.vercel.app"

MODES = {
    "book": {
        "dir": "book",
        "title": "HLD Gym: system design for senior interviews, free and complete",
        "desc": "A free, complete system design book for senior interviews. 51 chapters, "
                "197 animated diagrams and 1,278 questions, covering Meta, Google, Palantir "
                "and Anthropic loops. No signup, no paywall.",
        "og_title": "HLD Gym: system design for senior interviews",
        "og_desc": "51 chapters, 197 animated diagrams, 1,278 questions. Free, no signup.",
    },
    "origins": {
        "dir": "origins",
        "title": "Origins: where every idea in system design actually came from",
        "desc": "The same 51 chapters, each opening on the real dated event that forced "
                "the mechanism into its shape. Real people, real incidents, real sources. "
                "Free, no signup.",
        "og_title": "Origins — system design, told as the history it actually is",
        "og_desc": "Every idea traced to the room it came from. Free, no signup.",
    },
}

ALLOWED_TAGS = set("p h2 h3 ul ol li strong em code pre table thead tbody tr th td figure figcaption "
                   "svg g rect circle ellipse line path polyline polygon text tspan defs marker title "
                   "details summary div span dfn br blockquote".split())
ALLOWED_DIV = {"box", "box-tag", "analogy", "story", "lens", "crux", "feynman", "fey-prompt",
               "fey-model", "exercise", "ex-q", "takeaways", "diagram",
               "origin", "origin-seam", "origin-body", "card", "card-face", "card-back"}
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

def validate_html(cid, html, kind="chapter"):
    """kind is "chapter" or "origin". Origin fragments are the only place an
    <img> is permitted, and only pointing at the sibling assets directory."""
    if re.search(r'\bstyle\s*=', html): err(f"{cid}: inline style= forbidden")
    # No attribute allowlist exists, so an event handler would sail straight
    # through. Cheap to close, and permitting <img> is exactly when it matters.
    if re.search(r'<[^>]+\son[a-z]+\s*=', html): err(f"{cid}: event handler attribute forbidden")
    if "<img" in html:
        if kind != "origin":
            err(f"{cid}: <img> forbidden (use inline SVG)")
        else:
            for tag in re.findall(r'<img\b[^>]*>', html):
                src = re.search(r'\ssrc="([^"]*)"', tag)
                if not src or not src.group(1).startswith("assets/"):
                    err(f'{cid}: <img> src must start with "assets/"')
                if not re.search(r'\salt="[^"]', tag):
                    err(f"{cid}: <img> needs a non-empty alt")
    # The external-URL ban is unconditional; the assets/ check above is what
    # lets origin images through it, because a relative path has no scheme.
    if re.search(r'https?://', html): err(f"{cid}: external URL found")
    allowed = ALLOWED_TAGS | ({"img"} if kind == "origin" else set())
    for tag in re.findall(r'<([a-zA-Z][a-zA-Z0-9-]*)', html):
        if tag.lower() not in allowed:
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

CARD_SUITS = {"person", "incident", "artifact", "ripple"}

def validate_cards(cid, data):
    """A card is a Leitner item with a picture. Its id shares the namespace with
    quiz ids, so the prefix rule and the uniqueness rule are the same ones."""
    if data.get("chapter") != cid: err(f"{cid}: cards 'chapter' field mismatch")
    cards, seen = data.get("cards", []), set()
    for c in cards:
        cardid = c.get("id", "?")
        if cardid in seen: err(f"{cid}: duplicate card id {cardid}")
        seen.add(cardid)
        if not cardid.startswith(cid): err(f"{cid}: card id {cardid} must start with chapter id")
        if c.get("suit") not in CARD_SUITS: err(f"{cid}:{cardid}: suit must be one of {sorted(CARD_SUITS)}")
        if not isinstance(c.get("year"), int): err(f"{cid}:{cardid}: year must be an integer")
        for field in ("title", "body", "prompt", "answer", "cite"):
            if not str(c.get(field, "")).strip():
                err(f"{cid}:{cardid}: '{field}' is required")
        # A card with no prompt is a decoration, and decoration is the one thing
        # the design rules out. See the spec, "The deck".
        if len(str(c.get("body", "")).split()) > 60:
            err(f"{cid}:{cardid}: card body over 60 words")
        asset = c.get("asset")
        if asset and not str(asset).startswith("assets/"):
            err(f'{cid}:{cardid}: asset must start with "assets/"')
    return cards

def render(mode, toc, templates, quiz_all, cards_all, origins):
    """Compose one output. `mode` keys into MODES and lands on <body data-mode>,
    which is how app.js knows which view it is running as."""
    m = MODES[mode]
    canonical = f"{SITE}/{m['dir']}/"
    tpl = (SRC / "template.html").read_text()
    body = "\n".join(templates)
    if origins:
        body += "\n" + "\n".join(origins.values())
    return (tpl
        .replace("{{MODE}}", mode)
        .replace("{{PAGE_TITLE}}", m["title"])
        .replace("{{PAGE_DESC}}", m["desc"])
        .replace("{{CANONICAL}}", canonical)
        .replace("{{OG_TITLE}}", m["og_title"])
        .replace("{{OG_DESC}}", m["og_desc"])
        .replace("/*{{FONTS_CSS}}*/", font_css())
        .replace("/*{{STYLE_CSS}}*/", (SRC / "style.css").read_text())
        .replace("<!--{{CHAPTER_TEMPLATES}}-->", body)
        .replace("/*{{TOC_JSON}}*/", json.dumps(toc).replace("</", "<\\/"))
        .replace("/*{{QUIZ_JSON}}*/", json.dumps(quiz_all).replace("</", "<\\/"))
        .replace("/*{{CARDS_JSON}}*/", json.dumps(cards_all if mode == "origins" else {}).replace("</", "<\\/"))
        .replace("/*{{APP_JS}}*/", (SRC / "app.js").read_text().replace("</script", "<\\/script")))

def main():
    check_only = "--check" in sys.argv
    toc = json.loads((SRC / "toc.json").read_text())
    templates, quiz_all = [], {}
    cards_all, origins = {}, {}   # Tasks 4 and 3 fill these
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

            of = CH / f"{cid}.origin.html"
            if of.exists():
                ohtml = of.read_text()
                validate_html(cid, ohtml, "origin")
                words = len(re.sub(r"<[^>]+>", " ", ohtml).split())
                if words > 260:
                    err(f"{cid}: origin story is {words} words (limit 260)")
                origins[cid] = f'<template data-origin="{cid}">\n{ohtml}\n</template>'

            cf = CH / f"{cid}.cards.json"
            if cf.exists():
                try:
                    cards_all[cid] = validate_cards(cid, json.loads(cf.read_text()))
                except json.JSONDecodeError as e:
                    err(f"{cid}: cards json invalid: {e}")
            elif of.exists():
                # cards and story ship together — a story with no deck is a
                # chapter that got halfway
                err(f"{cid}: has .origin.html but no .cards.json")

    for w in warnings: print("WARN", w)
    if errors:
        for e in errors: print("FAIL", e)
        sys.exit(f"\n{len(errors)} error(s). Not building.")
    print(f"OK: {ready} chapters valid.")
    if check_only: return

    for mode, m in MODES.items():
        out = DIST / m["dir"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render(mode, toc, templates, quiz_all, cards_all, origins if mode == "origins" else {}))
        print(f"Built {out} ({out.stat().st_size / 1024:.0f} KB, {ready} chapters)")

if __name__ == "__main__":
    main()
