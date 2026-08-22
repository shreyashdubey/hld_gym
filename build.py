#!/usr/bin/env python3
"""Assemble dist/book/ and dist/origins/ from src/. Validates chapters + quizzes; fails loudly."""
import base64, json, re, shutil, sys
from pathlib import Path

ROOT = Path(__file__).parent
SRC = ROOT / "src"
CH = SRC / "chapters"
ASSETS = SRC / "assets"
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

# Every asset path an origin story or a card actually points at, filled by
# check_assets and consumed by copy_assets. src/assets/ is a source directory
# that agents also use as a scratchpad (licences.json, style-reference sketches),
# so shipping the directory wholesale published working notes. Copying only what
# is referenced is the only rule that stays correct when the next unnoticed file
# lands there; an extension allowlist would still have shipped ref-*.svg.
referenced = set()
IMAGE_EXTS = {".svg", ".webp", ".png", ".jpg", ".jpeg", ".avif", ".gif"}

def _is_year(v):
    # bool is a subclass of int in Python, so isinstance(True, int) is True and
    # a JSON `true` would sail through as a year. This is a history book, so a
    # year of 3 or 20260 is a typo, not a date.
    return isinstance(v, int) and not isinstance(v, bool) and 1800 <= v <= 2100

def check_assets(cid, html):
    """A broken image is a silent failure in the browser and a loud one here."""
    root = ASSETS.resolve()
    for ref in re.findall(r'(?:src|href)="([^"]+)"', html, re.I):
        if not ref.startswith("assets/"):
            continue
        p = (ASSETS / ref[len("assets/"):]).resolve()
        if not p.is_relative_to(root):
            err(f"{cid}: asset '{ref}' escapes src/assets/"); continue
        if not p.is_file():
            err(f"{cid}: asset '{ref}' does not exist in src/assets/"); continue
        referenced.add(p)

def unwired_images(assets_dir, referenced):
    """Image files nobody points at. The cost of copying only referenced files
    is that a drawn-but-unwired portrait silently does not ship, and 16 have
    gone missing that way before, so it warns rather than passing quietly."""
    return sorted(p for p in assets_dir.rglob("*")
                  if p.is_file() and p.suffix.lower() in IMAGE_EXTS and p.resolve() not in referenced)

def copy_assets(assets_dir, dest, referenced):
    """Copy exactly the referenced assets, nothing else. Returns what shipped."""
    shutil.rmtree(dest, ignore_errors=True)
    root = assets_dir.resolve()
    shipped = sorted(p for p in referenced if p.is_relative_to(root))
    for p in shipped:
        d = dest / p.relative_to(root)
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, d)
    return shipped

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
    if re.search(r'<[^>]+\son[a-z]+\s*=', html, re.IGNORECASE): err(f"{cid}: event handler attribute forbidden")
    if re.search(r'<img\b', html, re.I):
        if kind != "origin":
            err(f"{cid}: <img> forbidden (use inline SVG)")
        else:
            for tag in re.findall(r'<img\b[^>]*>', html, re.I):
                srcm = re.search(r'\ssrc="([^"]*)"', tag, re.I)
                if not srcm or not srcm.group(1).startswith("assets/"):
                    err(f'{cid}: <img> src must start with "assets/"')
                if not re.search(r'\salt="[^"]', tag, re.I):
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
    cards = data.get("cards", [])
    if not isinstance(cards, list):
        err(f"{cid}: cards 'cards' must be a list"); return []
    seen = set()
    for c in cards:
        cardid = c.get("id", "?")
        if cardid in seen: err(f"{cid}: duplicate card id {cardid}")
        seen.add(cardid)
        if not cardid.startswith(cid): err(f"{cid}: card id {cardid} must start with chapter id")
        if c.get("suit") not in CARD_SUITS: err(f"{cid}:{cardid}: suit must be one of {sorted(CARD_SUITS)}")
        if not _is_year(c.get("year")): err(f"{cid}:{cardid}: year must be an integer 1800-2100")
        for field in ("title", "sub", "body", "prompt", "answer", "cite"):
            if not str(c.get(field, "")).strip():
                err(f"{cid}:{cardid}: '{field}' is required")
        # A card with no prompt is a decoration, and decoration is the one thing
        # the design rules out. See the spec, "The deck".
        if len(str(c.get("body", "")).split()) > 60:
            err(f"{cid}:{cardid}: card body over 60 words")
        asset = c.get("asset")
        if asset and not str(asset).startswith("assets/"):
            err(f'{cid}:{cardid}: asset must start with "assets/"')
        # the path lands in an <img src> attribute. app.js sets it with
        # setAttribute so it cannot break out, but a quote or bracket here is a
        # typo either way, and the check_assets regex stops at the first quote.
        if asset and re.search(r"[\"'<>\s]", str(asset)):
            err(f"{cid}:{cardid}: asset must not contain quotes, angle brackets or whitespace")
    return cards

CITE_TYPES = {"paper", "rfc", "postmortem", "blog", "commit", "pr", "cve",
              "book", "talk", "docs", "oral-history", "news"}
# A blog post or a vendor doc is a source; it is not evidence. Recon caught
# vLLM's blog claiming 24x where the SOSP paper says 2-4x.
# `news` is contemporaneous journalism - a newspaper or trade report. For a
# pre-web event it is often the only contemporaneous record, and three authors
# typed such sources `blog` because nothing else fit. It is deliberately NOT
# primary: a newspaper reporting a hearing is not the hearing record, and a
# trade weekly reporting an outage is not the postmortem. Relaxing the primary
# bar so older events could clear it would gut the one gate that makes this mode
# credible - a chapter on a pre-web event still has to find a paper, a hearing
# record or an archive alongside its press coverage. Honest typing, same bar.
PRIMARY = {"paper", "rfc", "postmortem", "commit", "pr", "cve", "oral-history"}
# One matcher, both fact checks, deliberately lenient: `class="num fact"`, a
# reversed attribute order and `<SPAN CLASS="Fact">` are all fact spans. Lenient
# because a false failure on the requirement check costs an author a confusing
# build break. Shared because two matchers that disagree are worse than either
# one alone - a span the build counts as your citation then skipped the year
# check, which is the commonest failure in this content type. Opening tag only;
# the year check wraps it to capture the text.
FACT_SPAN = r'<span\b[^>]*class="[^"]*\bfact\b[^"]*"[^>]*>'

def validate_cites(cid, html, side, cards):
    """Offline integrity check. Never fetches: link-checking needs the network
    and must not live in a build."""
    src = side.get("sources", {})
    if not isinstance(src, dict):
        err(f"{cid}: cites 'sources' must be an object"); return
    if not isinstance(side.get("unverified", []), list):
        err(f"{cid}: cites 'unverified' must be a list"); return
    # A citation inside a comment is not a citation. Strip before scanning, or
    # `<!-- data-cite="x" -->` satisfies the gate this function exists to hold.
    live = re.sub(r'<!--.*?-->', '', html, flags=re.S)
    prose = set()   # keys the story itself cites
    for attr in re.findall(r'data-cite="([^"]+)"', live):
        for k in attr.split():
            prose.add(k)
            if k not in src: err(f"{cid}: data-cite '{k}' has no sidecar entry")
    # ...and at least one of them has to sit on a fact. `<p data-cite="k">` cited
    # nothing citable and dodged the year check below, which keys on .fact spans.
    # At least one, not all: a cite on the box or on a clause stays legal.
    facts = set()
    for tag in re.findall(FACT_SPAN, live, re.I):
        m = re.search(r'data-cite="([^"]+)"', tag)
        if m: facts.update(m.group(1).split())
    used = set(prose)   # prose + deck: what the sidecar cross-checks answer to
    for c in cards:
        k = c.get("cite")
        if k:
            used.add(k)
            if k not in src: err(f"{cid}:{c.get('id')}: cite '{k}' has no sidecar entry")
    # the gate: what the *prose* resolved, not what the text looks like. An empty
    # data-cite="" yields no key and must fail here, same as no data-cite at all.
    # Cards are excluded on purpose: `cite` is a required card field, so every
    # deck cites something and a gate that counted them could never fire.
    # Two mistakes, two messages: citing nothing is not the same error as citing
    # in the wrong place, and they need different corrections. Neither condition
    # asks the key to resolve - a dangling key is reported once, just above.
    if not prose:
        err(f"{cid}: origin prose carries no data-cite (card cites do not count)")
    elif not facts:
        err(f'{cid}: origin prose has data-cite but none on a <span class="fact"> '
            f'(at least one date, number or quoted string must carry its source)')
    for k, s in src.items():
        if s.get("type") not in CITE_TYPES: err(f"{cid}:{k}: type must be one of {sorted(CITE_TYPES)}")
        if not _is_year(s.get("year")): err(f"{cid}:{k}: year must be an integer 1800-2100")
        if not str(s.get("title", "")).strip(): err(f"{cid}:{k}: title is required")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(s.get("checked", ""))):
            err(f"{cid}:{k}: 'checked' must be an ISO date (YYYY-MM-DD)")
        # ~15-20% of primary sources 403 later; 'quote' is the exact string
        # captured at verification time, so a dead link never forces a re-hunt.
        if s.get("type") in PRIMARY and not str(s.get("quote", "")).strip():
            err(f"{cid}:{k}: primary sources need a 'quote' captured at verification time")
        if k not in used: warn(f"{cid}: source '{k}' is never cited")
    # ...and the primary source has to be one the story leans on. A card cannot
    # carry the chapter's only paper: the rule exists so the story rests on one.
    if prose and not any(src[k].get("type") in PRIMARY for k in prose if k in src):
        err(f"{cid}: origin prose cites no primary source (need one of {sorted(PRIMARY)})")
    # A date attached to the wrong source. Match the tag first, then pull
    # data-cite out of it - a hardcoded attribute order ("class=... data-cite=...")
    # is defeated by writing them the other way round.
    #
    # THE RULE IS ONE-DIRECTIONAL AND MUST STAY THAT WAY. Do not "fix" it back
    # into an equality test. A document cannot report an event that has not
    # happened yet, but it can report one that already has:
    #   text year > source year -> impossible, error. A 1985 report cannot
    #                              describe a 1990 event.
    #   text year < source year -> a retrospective source. A 2015 Fed paper
    #                              reconstructing a 1985 incident, a 2011 blog
    #                              recalling a 2010 decision. The normal case in
    #                              historical writing. Silent.
    #   equal                   -> fine.
    # The symmetric version fired on the normal case, and authors dodged it by
    # keeping dates out of .fact spans altogether - steering them away from the
    # exact construct O5 exists to encourage.
    #
    # Several years in one span ("between 1979 and 1998", "in 2006: everyone had
    # until 1 January 2007"): it fires only when *all* of them postdate the
    # source - hence min(), not max(). A document cannot report the past it did
    # not live through, but it very much can announce a future date: a deadline,
    # an effective date, a scheduled cutover. p3c01 is exactly that shape, an
    # ISO notice published in 2006 setting a 1 January 2007 implementation date,
    # and max() called it an error. One year in the span at or before the source
    # anchors the span in that document's own present, which makes a later year
    # in the same breath a forecast rather than an impossibility. When every
    # year postdates the source there is no anchor and no reading of that
    # document produces any of those dates.
    # ponytail: the ceiling is "1979 and 2005" cited to a 1998 source - 1979
    # anchors it, so 2005 goes unchecked. Tighten to per-year only if the
    # sidecar ever grows a field saying which year the fact is actually about;
    # without one, per-year fails the legitimate deadline case above.
    for tag, txt in re.findall(f'({FACT_SPAN})([^<]*)</span>', live, re.I):
        m = re.search(r'data-cite="([^" ]+)"', tag)
        if not m: continue
        k = m.group(1)
        years = [int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", txt)]
        sy = src[k].get("year") if k in src else None
        # _is_year, not truthiness: a source with a junk year is already reported
        # above, and `min(years) > "1985"` would crash the build instead.
        if years and _is_year(sy) and min(years) > sy:
            err(f"{cid}: fact '{txt[:40]}' dates {min(years)} to {k}, published {sy} "
                f"(a source cannot report an event later than itself)")

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
                check_assets(cid, ohtml)
                words = len(re.sub(r"<[^>]+>", " ", ohtml).split())
                if words > 260:
                    err(f"{cid}: origin story is {words} words (limit 260)")
                origins[cid] = f'<template data-origin="{cid}">\n{ohtml}\n</template>'

            cf = CH / f"{cid}.cards.json"
            if cf.exists():
                try:
                    cards_all[cid] = validate_cards(cid, json.loads(cf.read_text()))
                    for c in cards_all.get(cid, []):
                        if c.get("asset"):
                            check_assets(cid, f'src="{c["asset"]}"')
                except json.JSONDecodeError as e:
                    err(f"{cid}: cards json invalid: {e}")
            elif of.exists():
                # cards and story ship together — a story with no deck is a
                # chapter that got halfway
                err(f"{cid}: has .origin.html but no .cards.json")

            if of.exists():
                sf = CH / f"{cid}.cite.json"
                if not sf.exists():
                    err(f"{cid}: has .origin.html but no .cite.json")
                else:
                    try:
                        validate_cites(cid, ohtml, json.loads(sf.read_text()), cards_all.get(cid, []))
                    except json.JSONDecodeError as e:
                        err(f"{cid}: cite json invalid: {e}")

    if ASSETS.exists():
        for p in unwired_images(ASSETS, referenced):
            warn(f"asset '{p.name}' is referenced by no chapter or card — not shipped")

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

        if mode == "origins" and ASSETS.exists():
            dest = out.parent / "assets"
            n = len(copy_assets(ASSETS, dest, referenced))
            print(f"  copied {n} asset(s) → {dest}")

if __name__ == "__main__":
    main()
