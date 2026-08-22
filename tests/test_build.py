#!/usr/bin/env python3
"""Assert-based checks for build.py and the deploy wiring. No pytest in this repo.

Run: python3 tests/test_build.py
"""
import json, re, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_publish_excludes_other_pipelines():
    """sell's publish:book runs rsync --delete. Every directory another pipeline
    writes into dist/ needs an exclude or the next publish deletes it wholesale.
    origins/ was on this list until 2026-08-23, when the two book outputs became
    one and dist/origins/ stopped existing."""
    pkg = json.loads((ROOT / "sell" / "package.json").read_text())
    publish = pkg["scripts"]["publish:book"]
    assert "--delete" in publish, "publish:book no longer uses --delete; this test is stale"
    for d in ("book/", "reels/", "playground/"):
        assert f"--exclude '{d}'" in publish, f"publish:book is missing --exclude '{d}'"


def test_vercel_has_book_headers():
    cfg = json.loads((ROOT / "vercel.json").read_text())
    block = next((h for h in cfg["headers"] if h["source"] == "/book/(.*)"), None)
    assert block, "vercel.json has no cache rule for /book/"
    # not 'immutable': asset filenames are not content-hashed, so an immutable
    # rule would pin a stale image permanently
    values = {h["key"]: h["value"] for h in block["headers"]}
    assert values.get("Cache-Control") == "public, max-age=0, must-revalidate", \
        f"/book/ Cache-Control is {values.get('Cache-Control')!r}"


def test_vercel_redirects_the_retired_origins_url():
    """/origins/ was live and in the sitemap. Deleting the directory without a
    redirect 404s every link and index entry pointing at it."""
    cfg = json.loads((ROOT / "vercel.json").read_text())
    r = next((r for r in cfg.get("redirects", []) if r["source"].startswith("/origins/")), None)
    assert r, "vercel.json has no redirect for the retired /origins/ URL"
    assert r["destination"].startswith("/book/"), f"/origins/ points at {r['destination']!r}"
    assert r.get("permanent") is True, "the /origins/ redirect must be a 301, not a 307"


def test_sitemap_lists_the_book_and_not_origins():
    sm = (ROOT / "sell" / "app" / "sitemap.ts").read_text()
    body = sm.split("export default function sitemap")[1]
    assert "/book/" in body, "sitemap.ts does not list /book/"
    assert "/origins/" not in body, "sitemap.ts still lists /origins/, which now 301s"


def test_vercel_catchall_headers_stay_last():
    cfg = json.loads((ROOT / "vercel.json").read_text())
    assert cfg["headers"][-1]["source"] == "/(.*)", \
        "the catch-all security-header block must remain last in vercel.json"


def test_the_one_output_exists():
    """One build, one output. The second one at dist/origins/ was retired on
    2026-08-23; if it comes back, something is building the old two-mode loop."""
    book = ROOT / "dist" / "book" / "index.html"
    assert book.exists(), "dist/book/index.html missing — run python3 build.py"
    assert not (ROOT / "dist" / "origins").exists(), \
        "dist/origins/ is back — the two-mode build was meant to be one"


def test_output_runs_in_origins_mode():
    """The surviving output is the story-first one at the book's URL, so
    data-mode is 'origins' (the flag app.js reads) while the path is /book/."""
    book = (ROOT / "dist" / "book" / "index.html").read_text()
    assert '<body data-mode="origins">' in book, "output has no data-mode=origins"
    assert "hld-gym.vercel.app/book/" in book, "canonical is not /book/"
    assert "/origins/" not in book.split("</head>")[0], "<head> leaked a retired origins URL"


def test_no_unreplaced_placeholders():
    html = (ROOT / "dist" / "book" / "index.html").read_text()
    left = re.findall(r"\{\{[A-Z_]+\}\}", html)
    assert not left, f"unreplaced placeholders: {sorted(set(left))}"


def _a_shipping_origin():
    """A chapter that still has an origin layer, and its first card id.
    Discovered, not hard-coded: chapters get retired when they fail the O1 gate,
    and retiring one must not break the two tests below."""
    ch = ROOT / "src" / "chapters"
    cf = next(f for f in sorted(ch.glob("*.cards.json"))
              if (ch / f"{f.name.split('.')[0]}.origin.html").exists())
    return cf.name.split(".")[0], json.loads(cf.read_text())["cards"][0]["id"]


def test_origin_fragments_reach_the_book():
    book = (ROOT / "dist" / "book" / "index.html").read_text()
    cid, _ = _a_shipping_origin()
    # match the emitted element, not the bare attribute: app.js's
    # `template[data-origin="..."]` selector is not a fragment
    assert f'<template data-origin="{cid}">' in book, "origin fragment missing from the book"


def _validate(html, kind):
    """Drive build.py's validator directly. It accumulates into a module global,
    so reset it around each call."""
    sys.path.insert(0, str(ROOT))
    import build
    build.errors.clear()
    build.warnings.clear()
    build.validate_html("ptest", html, kind)
    return list(build.errors)


def test_img_rejected_in_chapter_allowed_in_origin():
    """Updated when inline figures landed: a bare <img> in a chapter is still
    rejected, but the reason is now "not in a figure" rather than "never", and
    width/height became mandatory for both kinds."""
    img = ('<p><img src="assets/lamport.webp" alt="Leslie Lamport in 1989" '
           'width="407" height="564"></p>')
    errs = _validate(img, "chapter")
    assert any("<img> forbidden" in e for e in errs), errs
    assert not _validate(img, "origin"), f"origin <img> wrongly rejected: {_validate(img, 'origin')}"


FIG = ('<figure class="fig" data-mode="origins">'
       '<img src="assets/photo/p2c10-mcilroy.jpg" alt="Doug McIlroy in 2011" '
       'width="407" height="564" loading="lazy">'
       '<figcaption>Doug McIlroy, who wrote the pipe into the shell overnight. '
       '<span class="credit">Photo Denise Panyik-Dale, CC BY 2.0</span></figcaption>'
       '</figure>')


def test_img_in_chapter_is_legal_only_inside_a_figure():
    """The whole point of the figure rule: the tag allowlist now contains <img>
    for both kinds, so the figure is the only thing keeping one out of prose."""
    assert not _validate(f"<h2>H</h2>{FIG}", "chapter"), \
        f"a well-formed figure was rejected: {_validate(f'<h2>H</h2>{FIG}', 'chapter')}"
    loose = '<p><img src="assets/photo/x.jpg" alt="A face" width="4" height="5"></p>'
    errs = _validate(loose, "chapter")
    assert any("forbidden outside a <figure" in e for e in errs), errs


def test_nested_figure_rejected():
    """Load-bearing, not cosmetic. The book render strips figures with a
    non-greedy `.*?</figure>`; a nested figure would close that match on the
    inner tag and delete the rest of the chapter. This check is what makes the
    regex safe, so it has to fail the build."""
    nested = FIG.replace('<figcaption>', '<figure class="diagram"><svg/></figure><figcaption>')
    errs = _validate(nested, "chapter")
    assert any("nested inside a <figure>" in e for e in errs), errs
    # a sibling figure after the first is not nesting and must stay legal
    assert not _validate(f'{FIG}<figure class="diagram"><svg/></figure>', "chapter"), \
        "two sibling figures were mistaken for nesting"


def test_figure_shape_rules():
    two = FIG.replace('<figcaption>',
                      '<img src="assets/photo/y.jpg" alt="B" width="1" height="1"><figcaption>')
    assert any("exactly one <img>" in e for e in _validate(two, "chapter")), _validate(two, "chapter")
    nocap = FIG.replace('<figcaption>Doug McIlroy, who wrote the pipe into the shell overnight. '
                        '<span class="credit">Photo Denise Panyik-Dale, CC BY 2.0</span></figcaption>', '')
    assert any("needs a <figcaption>" in e for e in _validate(nocap, "chapter")), _validate(nocap, "chapter")
    nocredit = FIG.replace('<span class="credit">Photo Denise Panyik-Dale, CC BY 2.0</span>', '')
    assert any('<span class="credit">' in e for e in _validate(nocredit, "chapter")), _validate(nocredit, "chapter")
    empty = FIG.replace('Photo Denise Panyik-Dale, CC BY 2.0</span>', '</span>')
    assert _validate(empty, "chapter"), "an empty credit span must be rejected"


def test_figure_img_needs_intrinsic_size():
    """Without both, the reading column reflows as each image arrives."""
    for bad in ('width="407"', 'width="407" height="0"', 'width="wide" height="564"'):
        f = FIG.replace('width="407" height="564"', bad)
        errs = _validate(f, "chapter")
        assert any("positive integer" in e for e in errs), (bad, errs)


def test_origin_img_must_be_relative_and_described():
    external = '<p><img src="https://example.com/x.jpg" alt="x"></p>'
    errs = _validate(external, "origin")
    assert any('src must start with "assets/"' in e for e in errs), errs
    bare = '<p><img src="/other/x.webp" alt="x"></p>'
    assert _validate(bare, "origin"), "img src outside assets/ must be rejected"
    noalt = '<p><img src="assets/x.webp"></p>'
    assert _validate(noalt, "origin"), "img without alt must be rejected"


def test_event_handler_attributes_rejected_everywhere():
    """build.py has no attribute allowlist at all. Allowing <img> without this
    check would make an author typo an injection."""
    for kind in ("chapter", "origin"):
        assert _validate('<p onclick="alert(1)">x</p>', kind), f"on*= not caught in {kind}"


def test_event_handler_attributes_are_case_insensitive():
    for kind in ("chapter", "origin"):
        assert _validate('<p onClick="alert(1)">x</p>', kind), f"onClick not caught in {kind}"
        assert _validate('<p ONMOUSEOVER="x">y</p>', kind), f"ONMOUSEOVER not caught in {kind}"


def test_uppercase_img_tag_still_enforces_origin_rules():
    """Same bug class as the event-handler case-sensitivity fix, one line up:
    if kind detection is case-sensitive, so is everything gated behind it."""
    assert _validate('<p><IMG SRC="/other/x.webp"></p>', "origin"), \
        "uppercase IMG must still enforce assets/ + alt in origin fragments"
    assert _validate('<p><Img src="assets/x.webp"></p>', "origin"), \
        "mixed-case Img must still require a non-empty alt"
    assert _validate('<p><IMG src="assets/x.webp" alt="d"></p>', "chapter"), \
        "uppercase IMG must still be forbidden in chapter fragments"


CARD_OK = {
    "chapter": "ptest",
    "cards": [
        {"id": "ptest-c1", "suit": "person", "title": "A Person", "sub": "1989 · Somewhere",
         "year": 1989, "body": "Short face text.", "prompt": "What did they hit?",
         "answer": "The constraint.", "cite": "src1"},
    ],
}


def _validate_cards(data):
    sys.path.insert(0, str(ROOT))
    import build
    build.errors.clear()
    build.validate_cards("ptest", data)
    return list(build.errors)


def test_good_card_passes():
    assert not _validate_cards(CARD_OK), _validate_cards(CARD_OK)


def test_card_id_must_be_chapter_prefixed():
    bad = json.loads(json.dumps(CARD_OK))
    bad["cards"][0]["id"] = "other-c1"
    assert _validate_cards(bad)


def test_card_suit_must_be_known():
    bad = json.loads(json.dumps(CARD_OK))
    bad["cards"][0]["suit"] = "vibes"
    assert _validate_cards(bad)


def test_card_needs_prompt_and_answer():
    """A card without a recall prompt is a decoration. The gate is the whole
    justification for cards existing at all."""
    for field in ("prompt", "answer"):
        bad = json.loads(json.dumps(CARD_OK))
        del bad["cards"][0][field]
        assert _validate_cards(bad), f"missing {field} was accepted"


def test_card_needs_sub():
    """sub carries the date and place - the field that makes a card historical
    rather than trivia."""
    bad = json.loads(json.dumps(CARD_OK))
    del bad["cards"][0]["sub"]
    assert _validate_cards(bad), "missing sub was accepted"
    bad = json.loads(json.dumps(CARD_OK))
    bad["cards"][0]["sub"] = ""
    assert _validate_cards(bad), "empty sub was accepted"


def test_card_year_rejects_bool_string_and_out_of_range():
    """bool is a subclass of int in Python, so isinstance(True, int) is True -
    a JSON `true` must not sail through as a year."""
    bad = json.loads(json.dumps(CARD_OK)); bad["cards"][0]["year"] = True
    assert _validate_cards(bad), "year: true was accepted"
    bad = json.loads(json.dumps(CARD_OK)); bad["cards"][0]["year"] = "1989"
    assert _validate_cards(bad), "year as a string was accepted"
    bad = json.loads(json.dumps(CARD_OK)); bad["cards"][0]["year"] = 3
    assert _validate_cards(bad), "an out-of-range year (3) was accepted"


def test_card_body_capped_at_60_words():
    bad = json.loads(json.dumps(CARD_OK))
    bad["cards"][0]["body"] = "word " * 61
    assert _validate_cards(bad)


def test_card_asset_must_be_relative():
    bad = json.loads(json.dumps(CARD_OK))
    bad["cards"][0]["asset"] = "https://example.com/x.webp"
    assert _validate_cards(bad)


def test_card_asset_rejects_attribute_breakers():
    """The path lands in an <img src>. A quote would close the attribute, and
    check_assets' regex stops at the first quote so it would not catch it."""
    for bad_asset in ('assets/x.webp" onerror="alert(1)',
                      "assets/x.webp' onerror='alert(1)",
                      "assets/<script>.webp",
                      "assets/two words.webp"):
        bad = json.loads(json.dumps(CARD_OK))
        bad["cards"][0]["asset"] = bad_asset
        assert _validate_cards(bad), f"accepted asset {bad_asset!r}"
    ok = json.loads(json.dumps(CARD_OK))
    ok["cards"][0]["asset"] = "assets/fine-name_1.webp"
    assert not _validate_cards(ok), "rejected a clean asset path"


def test_cards_object_instead_of_list_fails_cleanly():
    """{"cards": {"a": {...}}} - an object where a list belongs - must fail
    the build, not raise. A validator that crashes tells an author nothing
    about which file is wrong."""
    sys.path.insert(0, str(ROOT))
    import build
    build.errors.clear()
    build.validate_cards("ptest", {"chapter": "ptest", "cards": {"a": {"id": "x"}}})
    assert build.errors, "a 'cards' object instead of a list should fail, not crash"


def test_cards_reach_the_book():
    book = (ROOT / "dist" / "book" / "index.html").read_text()
    _, card = _a_shipping_origin()
    assert f'"{card}"' in book, "cards missing from the book"


CITE_OK = {
    "chapter": "ptest",
    "sources": {
        "src1": {"type": "paper", "title": "A Paper", "year": 1998,
                 "url": "https://example.com/p", "checked": "2026-08-22",
                 "quote": "exact string from the source"},
    },
    "unverified": [],
}


def _validate_cites(html, side, cards=()):
    sys.path.insert(0, str(ROOT))
    import build
    build.errors.clear()
    build.warnings.clear()
    build.validate_cites("ptest", html, side, list(cards))
    return list(build.errors)


def test_good_sidecar_passes():
    html = '<div class="box origin"><p><span class="fact" data-cite="src1">1998</span></p></div>'
    assert not _validate_cites(html, CITE_OK), _validate_cites(html, CITE_OK)


def test_empty_data_cite_value_fails():
    """data-cite="" is the most direct fake: the presence of the literal
    attribute text must not stand in for an id that actually resolved."""
    html = '<div class="box origin"><p><span class="fact" data-cite="">1998</span></p></div>'
    assert _validate_cites(html, CITE_OK), "an empty data-cite value was accepted"


def test_commented_out_citation_fails():
    """A citation inside an HTML comment is not a citation."""
    html = ('<div class="box origin"><!-- <span class="fact" data-cite="src1">1998</span> -->'
            '<p>no real cite</p></div>')
    assert _validate_cites(html, CITE_OK), "a commented-out data-cite satisfied the gate"


def test_dangling_data_cite_fails():
    html = '<div class="box origin"><p><span class="fact" data-cite="ghost">x</span></p></div>'
    errs = _validate_cites(html, CITE_OK)
    assert any("ghost" in e and "sidecar" in e for e in errs), errs


def test_origin_box_without_any_cite_fails():
    html = '<div class="box origin"><p>Confident history, no source.</p></div>'
    assert _validate_cites(html, CITE_OK)


def test_primary_source_required():
    side = json.loads(json.dumps(CITE_OK))
    side["sources"]["src1"]["type"] = "blog"
    html = '<div class="box origin"><p><span class="fact" data-cite="src1">1998</span></p></div>'
    assert _validate_cites(html, side), "a chapter cited only to a blog should fail"


def test_year_mismatch_between_text_and_source():
    html = '<div class="box origin"><p><span class="fact" data-cite="src1">1989</span></p></div>'
    assert _validate_cites(html, CITE_OK), "1989 in text against a 1998 source should fail"


def test_year_mismatch_caught_regardless_of_attribute_order():
    """The check must not hardcode 'class="fact" data-cite=...' - writing the
    two attributes the other way round must not dodge it."""
    html = '<div class="box origin"><p><span data-cite="src1" class="fact">1989</span></p></div>'
    assert _validate_cites(html, CITE_OK), "reversed attribute order dodged the year check"


def test_checked_date_required_and_iso():
    side = json.loads(json.dumps(CITE_OK))
    side["sources"]["src1"]["checked"] = "last tuesday"
    html = '<div class="box origin"><p><span class="fact" data-cite="src1">1998</span></p></div>'
    assert _validate_cites(html, side)


def test_primary_source_requires_quote():
    """~15-20% of primary sources 403 later; 'quote' is captured at
    verification time so a dead link never forces a re-hunt. Enforce it."""
    side = json.loads(json.dumps(CITE_OK))
    del side["sources"]["src1"]["quote"]
    html = '<div class="box origin"><p><span class="fact" data-cite="src1">1998</span></p></div>'
    assert _validate_cites(html, side), "a primary source with no quote was accepted"


def test_secondary_source_quote_is_optional():
    side = json.loads(json.dumps(CITE_OK))
    side["sources"]["src2"] = {"type": "blog", "title": "A Blog", "year": 1998,
                                "checked": "2026-08-22"}
    html = ('<div class="box origin"><p><span class="fact" data-cite="src1">1998</span></p>'
            '<p><span class="fact" data-cite="src2">1998</span></p></div>')
    errs = _validate_cites(html, side)
    assert not any("quote" in e for e in errs), errs


def test_source_year_rejects_bool_and_out_of_range():
    side = json.loads(json.dumps(CITE_OK)); side["sources"]["src1"]["year"] = True
    html = '<div class="box origin"><p><span class="fact" data-cite="src1">1998</span></p></div>'
    assert _validate_cites(html, side), "source year: true was accepted"
    side = json.loads(json.dumps(CITE_OK)); side["sources"]["src1"]["year"] = 20260
    assert _validate_cites(html, side), "an out-of-range source year (20260) was accepted"


def test_card_cite_must_resolve():
    html = '<div class="box origin"><p><span class="fact" data-cite="src1">1998</span></p></div>'
    cards = [{"id": "ptest-c1", "cite": "nowhere"}]
    assert _validate_cites(html, CITE_OK, cards)


def test_nested_div_inside_origin_box_still_finds_cite():
    """The box-tag div nests inside the origin box. A naive non-greedy regex
    stops at its </div> and never reaches the citation."""
    html = ('<div class="box origin"><div class="box-tag">Place, 1998</div>'
            '<p><span class="fact" data-cite="src1">1998</span></p></div>')
    assert not _validate_cites(html, CITE_OK), _validate_cites(html, CITE_OK)


def test_sources_non_dict_fails_cleanly():
    errs = _validate_cites("<div class='box origin'></div>",
                            {"chapter": "ptest", "sources": ["not", "a", "dict"]})
    assert errs, "a non-object 'sources' should fail, not crash"


def test_unverified_non_list_fails_cleanly():
    errs = _validate_cites("<div class='box origin'></div>",
                            {"chapter": "ptest", "sources": {}, "unverified": "nope"})
    assert errs, "a non-list 'unverified' should fail, not crash"


def test_referenced_assets_reach_the_book():
    """Was test_assets_copied_to_origins, which asserted that *every* file in
    src/assets/ ships - the assertion that put licences.json on the open
    internet. What must ship is what a card or an origin story points at."""
    src = ROOT / "src" / "assets"
    dst = ROOT / "dist" / "book" / "assets"
    refs = set()
    for f in (ROOT / "src" / "chapters").iterdir():
        if f.name.endswith((".cards.json", ".origin.html")):
            refs |= set(re.findall(r'"assets/([^"]+)"', f.read_text()))
    refs = {r for r in refs if (src / r).is_file()}
    if not refs:
        return  # nothing wired up yet; the missing-asset test below is the real guard
    for r in sorted(refs):
        assert (dst / r).exists(), f"{r} is referenced but missing from dist/book/assets/"


def test_missing_asset_is_a_build_error():
    sys.path.insert(0, str(ROOT))
    import build
    build.errors.clear()
    build.check_assets("ptest", '<p><img src="assets/does-not-exist.webp" alt="x"></p>')
    assert build.errors, "a reference to a nonexistent asset should fail the build"


def test_check_assets_rejects_path_traversal():
    """src="assets/../../build.py" passed both the prefix check and the
    existence check, then was never copied into dist/book/assets/ - a
    broken image the build called fine."""
    sys.path.insert(0, str(ROOT))
    import build
    build.errors.clear()
    build.check_assets("ptest", '<img src="assets/../../build.py" alt="x">')
    assert build.errors, "a path escaping src/assets/ should fail the build"


def test_check_assets_rejects_a_directory():
    """src="assets/somedir" must not pass just because the path exists."""
    sys.path.insert(0, str(ROOT))
    import build
    build.errors.clear()
    build.check_assets("ptest", '<img src="assets/" alt="x">')
    assert build.errors, "a directory reference should fail the build"

def test_prose_with_no_cite_fails_even_when_cards_cite():
    """The gate is on the story, not the deck. `cite` is a required card field,
    so every deck cites something and folding card keys into the gate made it
    unfirable: an origin story with zero sourced claims sailed through."""
    html = '<div class="box origin"><p>Confident history, no source.</p></div>'
    cards = [{"id": "ptest-c1", "cite": "src1"}]
    assert _validate_cites(html, CITE_OK, cards), "an unsourced story passed because its cards cited"


def test_empty_prose_cite_fails_even_when_cards_cite():
    """data-cite="" yields no key. A citing card must not paper over it."""
    html = '<div class="box origin"><p><span class="fact" data-cite="">1998</span></p></div>'
    cards = [{"id": "ptest-c1", "cite": "src1"}]
    assert _validate_cites(html, CITE_OK, cards), 'data-cite="" plus a citing card passed the gate'


def test_primary_source_must_be_cited_in_prose():
    """A card cannot carry the chapter's only primary source. The rule exists so
    the *story* rests on a paper, RFC, postmortem, commit, PR, CVE or oral history."""
    side = json.loads(json.dumps(CITE_OK))
    side["sources"]["blog1"] = {"type": "blog", "title": "A Blog", "year": 1998,
                                "checked": "2026-08-22"}
    html = '<div class="box origin"><p><span class="fact" data-cite="blog1">1998</span></p></div>'
    cards = [{"id": "ptest-c1", "cite": "src1"}]   # src1 is the paper
    errs = _validate_cites(html, side, cards)
    assert any("primary" in e for e in errs), errs


def test_prose_primary_cite_with_cards_passes_clean():
    """The shape a real chapter has: prose on the paper, deck citing too."""
    html = '<div class="box origin"><p><span class="fact" data-cite="src1">1998</span></p></div>'
    cards = [{"id": "ptest-c1", "cite": "src1"}]
    assert not _validate_cites(html, CITE_OK, cards), _validate_cites(html, CITE_OK, cards)


def test_commented_cite_is_not_a_prose_citation():
    """Comments are stripped before the scan, so a commented cite is not prose -
    and a citing card must not stand in for the one the author commented out."""
    html = ('<div class="box origin"><!-- <span class="fact" data-cite="src1">1998</span> -->'
            '<p>no real cite</p></div>')
    cards = [{"id": "ptest-c1", "cite": "src1"}]
    assert _validate_cites(html, CITE_OK, cards), "a commented-out cite plus a citing card passed"

def test_data_cite_on_non_fact_element_fails():
    """`<p data-cite="key">` satisfied the prose gate while citing no citable
    fact, and dodged the year-agreement check, which keys on `.fact` spans.
    At least one citation has to sit on a fact."""
    html = '<div class="box origin"><p data-cite="src1">Confident history.</p></div>'
    errs = _validate_cites(html, CITE_OK)
    assert any("fact" in e for e in errs), errs
    assert not any("carries no data-cite" in e for e in errs), \
        f"wrong diagnosis: this author cited something, just not on a fact. {errs}"


def test_one_fact_span_is_enough_alongside_other_cites():
    """The bound: *at least one* fact span, not all citations on fact spans. A
    story-level cite on the box, or one attached to a clause, stays legal."""
    html = ('<div class="box origin" data-cite="src1"><p data-cite="src1">A clause.</p>'
            '<p><span class="fact" data-cite="src1">1998</span></p></div>')
    assert not _validate_cites(html, CITE_OK), _validate_cites(html, CITE_OK)


def test_fact_span_with_dangling_key_reports_only_the_dangling_key():
    """An unresolved key on a fact span is a dangling-citation error. The
    fact-span condition is satisfied - the span is there - so do not also
    report it missing and send the author looking for the wrong mistake."""
    html = '<div class="box origin"><p><span class="fact" data-cite="ghost">1998</span></p></div>'
    errs = _validate_cites(html, CITE_OK)
    assert any("ghost" in e and "sidecar" in e for e in errs), errs
    assert not any("carries no data-cite" in e or 'class="fact"' in e for e in errs), \
        f"double-reported one mistake as two. {errs}"

def test_year_check_reads_a_multi_class_fact_span():
    """The requirement check and the year check must agree on what a fact span
    is. When only the requirement check was lenient, `class="num fact"` counted
    as the chapter's citation and then silently skipped the year check - the
    spec calls year drift the single commonest failure in this content type."""
    html = '<div class="box origin"><p><span class="num fact" data-cite="src1">1989</span></p></div>'
    errs = _validate_cites(html, CITE_OK)
    assert any("1989" in e for e in errs), f"multi-class fact span dodged the year check: {errs}"


def test_year_check_reads_a_multi_class_span_with_reversed_attributes():
    html = '<div class="box origin"><p><span data-cite="src1" class="num fact">1989</span></p></div>'
    errs = _validate_cites(html, CITE_OK)
    assert any("1989" in e for e in errs), f"reversed order + multi-class dodged the year check: {errs}"


def test_year_check_is_case_insensitive_like_the_requirement_check():
    html = '<div class="box origin"><p><span CLASS="Num Fact" data-cite="src1">1989</span></p></div>'
    errs = _validate_cites(html, CITE_OK)
    assert any("1989" in e for e in errs), f"uppercase multi-class dodged the year check: {errs}"


def test_both_fact_checks_share_one_matcher():
    """Any span the requirement check accepts as the chapter's citation must be
    a span the year check reads. Asserted over the shapes an author might write,
    so the two can never drift apart again unnoticed."""
    for cls, attrs in (('class="fact"', ''), ('class="num fact"', ''),
                       ('class="fact big"', ''), ('CLASS="Fact"', ''),
                       ('class="num fact"', 'id="x" ')):
        html = f'<div class="box origin"><p><span {attrs}{cls} data-cite="src1">1989</span></p></div>'
        errs = _validate_cites(html, CITE_OK)
        assert not any('class="fact"' in e for e in errs), \
            f"{cls} was not accepted as a citation: {errs}"
        assert any("1989" in e for e in errs), \
            f"{cls} was accepted as a citation but its year went unchecked: {errs}"


def _build():
    sys.path.insert(0, str(ROOT))
    import build
    return build


def _asset_fixture(td):
    """A src/assets/ in miniature: one wired portrait, one working note, one
    portrait nobody wired up."""
    src = Path(td) / "assets"
    src.mkdir()
    (src / "p9c99-person.svg").write_text("<svg/>")
    (src / "licences.json").write_text('{"note": "internal"}')
    (src / "p9c98-person.svg").write_text("<svg/>")
    return src, Path(td) / "dist" / "assets", {(src / "p9c99-person.svg").resolve()}


def test_working_file_does_not_reach_dist():
    """licences.json is an internal triage note naming which Commons files are
    mis-licensed. It is a working file in a source directory, and the wholesale
    copytree published it."""
    build = _build()
    with tempfile.TemporaryDirectory() as td:
        src, dest, referenced = _asset_fixture(td)
        build.copy_assets(src, dest, referenced)
        assert not (dest / "licences.json").exists(), "a .json working file reached the public output"


def test_shipped_assets_contain_no_working_files():
    """The same guard against the real built site, not a fixture."""
    build = _build()
    dst = ROOT / "dist" / "book" / "assets"
    if not dst.exists():
        return  # nothing built; test_the_one_output_exists is the guard for that
    stray = sorted(p.name for p in dst.rglob("*")
                   if p.is_file() and p.suffix.lower() not in build.IMAGE_EXTS)
    assert not stray, f"non-image working files reached dist/book/assets/: {stray}"


def test_referenced_svg_does_reach_dist():
    build = _build()
    with tempfile.TemporaryDirectory() as td:
        src, dest, referenced = _asset_fixture(td)
        shipped = build.copy_assets(src, dest, referenced)
        assert (dest / "p9c99-person.svg").exists(), "a referenced .svg was not copied"
        assert [p.name for p in shipped] == ["p9c99-person.svg"], \
            f"copy_assets shipped more than the referenced set: {[p.name for p in shipped]}"


def test_unreferenced_image_warns_and_does_not_ship():
    """The cost of copying only referenced files: a drawn portrait nobody wired
    up silently vanishes. 16 went missing once already, so it must be loud."""
    build = _build()
    with tempfile.TemporaryDirectory() as td:
        src, dest, referenced = _asset_fixture(td)
        build.copy_assets(src, dest, referenced)
        assert not (dest / "p9c98-person.svg").exists(), "an unreferenced image shipped anyway"
        unwired = [p.name for p in build.unwired_images(src, referenced)]
        assert unwired == ["p9c98-person.svg"], \
            f"an unreferenced portrait was not surfaced (or a working file was): {unwired}"


def _manifest_check(td, manifests, files=(), refs=(), figs=()):
    """Point build.py at a throwaway src/assets/ and run the manifest gate.
    check_manifest reads module globals, so save and restore them or the next
    test in the run inherits a fake assets directory."""
    build = _build()
    saved = (build.ASSETS, build.referenced, build.figures)
    try:
        assets = Path(td) / "assets"
        (assets / "photo").mkdir(parents=True, exist_ok=True)
        (assets / "mark").mkdir(parents=True, exist_ok=True)
        for name, entries in manifests.items():
            (assets / name).write_text(json.dumps({"entries": entries}))
        for f in files:
            (assets / f).write_text("x")
        build.ASSETS = assets
        build.referenced = {(assets / r).resolve() for r in refs}
        build.figures = list(figs)
        build.errors.clear()
        build.warnings.clear()
        build.check_manifest(build.load_manifests())
        return list(build.errors), list(build.warnings)
    finally:
        build.ASSETS, build.referenced, build.figures = saved
        build.errors.clear()
        build.warnings.clear()


ROW = {"kind": "person", "subject": "M. Douglas McIlroy", "licence": "CC BY 2.0",
       "credit": "Photo Denise Panyik-Dale, CC BY 2.0",
       "source": "https://commons.wikimedia.org/wiki/File:Douglas_McIlroy.jpeg",
       "retrieved": "2026-08-22"}
MARK_ROW = {"kind": "mark", "subject": "Google", "licence": "Public domain",
            "credit": "Google wordmark, public domain", "source": "https://example.org/g",
            "retrieved": "2026-08-22", "trademark": "Google LLC"}


def test_no_manifests_at_all_is_valid():
    """Zero photographs is the state the book shipped in for a year. It must
    pass, or nobody can build until the first photo lands."""
    with tempfile.TemporaryDirectory() as td:
        errs, _ = _manifest_check(td, {})
        assert not errs, errs


def test_photo_without_manifest_row_is_an_error():
    """The only thing between this project and an unattributed photograph going
    live. It errors; it does not warn."""
    with tempfile.TemporaryDirectory() as td:
        errs, _ = _manifest_check(td, {}, files=("photo/x.jpg",), refs=("photo/x.jpg",))
        assert any("photo/x.jpg" in e and "no manifest row" in e for e in errs), errs
    # an authored drawing owes nothing and must stay silent
    with tempfile.TemporaryDirectory() as td:
        errs, _ = _manifest_check(td, {}, files=("p9c99-person.svg",), refs=("p9c99-person.svg",))
        assert not errs, errs


def test_duplicate_manifest_key_names_both_files():
    with tempfile.TemporaryDirectory() as td:
        errs, _ = _manifest_check(td, {"a.manifest.json": {"photo/x.jpg": ROW},
                                       "b.manifest.json": {"photo/x.jpg": ROW}},
                                  files=("photo/x.jpg",))
        assert any("a.manifest.json" in e and "b.manifest.json" in e for e in errs), errs


def test_mark_row_missing_trademark_is_rejected():
    """A free copyright status does not make a mark unencumbered. The owner has
    to be named, so the field is mandatory for kind=mark and only for that."""
    row = dict(MARK_ROW)
    del row["trademark"]
    with tempfile.TemporaryDirectory() as td:
        errs, _ = _manifest_check(td, {"m.manifest.json": {"mark/g.svg": row}},
                                  files=("mark/g.svg",), refs=("mark/g.svg",))
        assert any("trademark" in e for e in errs), errs
    with tempfile.TemporaryDirectory() as td:
        errs, _ = _manifest_check(td, {"m.manifest.json": {"mark/g.svg": MARK_ROW}},
                                  files=("mark/g.svg",), refs=("mark/g.svg",))
        assert not errs, errs
    # a person row is not asked for a trademark
    with tempfile.TemporaryDirectory() as td:
        errs, _ = _manifest_check(td, {"m.manifest.json": {"photo/x.jpg": ROW}},
                                  files=("photo/x.jpg",), refs=("photo/x.jpg",))
        assert not errs, errs


def test_manifest_row_missing_fields_lists_them():
    row = dict(ROW)
    del row["licence"]
    row["retrieved"] = "  "
    with tempfile.TemporaryDirectory() as td:
        errs, _ = _manifest_check(td, {"m.manifest.json": {"photo/x.jpg": row}},
                                  files=("photo/x.jpg",), refs=("photo/x.jpg",))
        assert any("licence" in e and "retrieved" in e for e in errs), errs


def test_manifest_row_with_no_file_or_no_reference_only_warns():
    """Neither is a publication problem: nothing shipped."""
    with tempfile.TemporaryDirectory() as td:
        errs, warns = _manifest_check(td, {"m.manifest.json": {"photo/gone.jpg": ROW}})
        assert not errs, errs
        assert any("no such file" in w for w in warns), warns
    with tempfile.TemporaryDirectory() as td:
        errs, warns = _manifest_check(td, {"m.manifest.json": {"photo/x.jpg": ROW}},
                                      files=("photo/x.jpg",))
        assert not errs, errs
        assert any("nothing references it" in w for w in warns), warns


def test_figcaption_credit_must_match_the_manifest():
    """The attribution that ships has to be the attribution someone verified,
    not a retyping of it."""
    fig = ("ptest", "assets/photo/x.jpg", "Photo Denise Panyik-Dale, CC BY 2.5")
    with tempfile.TemporaryDirectory() as td:
        errs, _ = _manifest_check(td, {"m.manifest.json": {"photo/x.jpg": ROW}},
                                  files=("photo/x.jpg",), refs=("photo/x.jpg",), figs=[fig])
        assert any("does not match the manifest" in e for e in errs), errs
        joined = "\n".join(errs)
        assert "CC BY 2.5" in joined and "CC BY 2.0" in joined, \
            f"the mismatch error must print both strings: {joined}"


def test_figcaption_credit_survives_entities_and_wrapping():
    """An author writes &amp; where the manifest has &, and wraps a long credit
    across source lines. Neither is a different attribution."""
    row = dict(ROW, credit="Photo Panyik-Dale & Sons, CC BY 2.0")
    fig = ("ptest", "assets/photo/x.jpg", "Photo Panyik-Dale &amp; Sons,\n      CC BY 2.0")
    with tempfile.TemporaryDirectory() as td:
        errs, _ = _manifest_check(td, {"m.manifest.json": {"photo/x.jpg": row}},
                                  files=("photo/x.jpg",), refs=("photo/x.jpg",), figs=[fig])
        assert not errs, errs


def _render(templates):
    build = _build()
    return build.render({"parts": []}, templates, {}, {}, {})


def test_render_keeps_inline_figures():
    """There was a second render that stripped these out, for the /book output
    that shipped no images. That output is gone; every figure now reaches the
    page it was written for."""
    fig = ('<figure class="fig" data-mode="origins">'
           '<img src="assets/photo/x.jpg" alt="A face" width="4" height="5">'
           '<figcaption>A sentence. <span class="credit">C</span></figcaption></figure>')
    tpl = [f'<template data-ch="ptest"><h2>H</h2><p>before</p>{fig}<p>after</p></template>']
    html = _render(tpl)
    assert "assets/photo/x.jpg" in html, "the render dropped an inline figure"
    assert "A sentence." in html, "the render dropped a figcaption"
    assert "<p>before</p>" in html and "<p>after</p>" in html, "the render ate surrounding prose"


def test_credits_block_reflects_only_what_ships():
    """A build that ships no image files gets no credits block at all. An empty
    table is a claim about images that are not on the page. This was /book's
    normal state until the two outputs merged; it is now the fixture case."""
    build = _build()
    with tempfile.TemporaryDirectory() as td:
        saved = build.ASSETS
        try:
            assets = Path(td) / "assets"
            (assets / "photo").mkdir(parents=True)
            (assets / "mark").mkdir(parents=True)
            (assets / "photo" / "x.jpg").write_text("x")
            (assets / "mark" / "g.svg").write_text("x")
            (assets / "p9c99-person.svg").write_text("<svg/>")
            build.ASSETS = assets
            entries = {"photo/x.jpg": ROW, "mark/g.svg": MARK_ROW}
            ship = [(assets / r).resolve()
                    for r in ("photo/x.jpg", "mark/g.svg", "p9c99-person.svg")]
            assert build.credits_html(entries, [], 197) == "", \
                "a mode that ships no images still rendered a credits block"
            html = build.credits_html(entries, ship, 197)
            assert 'aria-labelledby="credits-h"' in html and "<footer" in html, html[:200]
            assert "M. Douglas McIlroy" in html and "CC BY 2.0" in html, "table row missing"
            assert "197 diagrams" in html, "the diagram count is not computed"
            assert "1 of the images" in html, "the authored-portrait count is not computed"
            assert "trademarks of their owners" in html, \
                "a mark shipped without the trademark paragraph"
            # ...and no trademark paragraph when no mark ships
            photos_only = build.credits_html(entries, ship[:1] + ship[2:], 197)
            assert "trademarks of their owners" not in photos_only, \
                "the trademark paragraph rendered with no mark on the page"
        finally:
            build.ASSETS = saved


def main():
    failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"ok   {name}")
            except AssertionError as e:
                failed += 1
                print(f"FAIL {name}: {e}")
    if failed:
        sys.exit(f"\n{failed} test(s) failed.")
    print("\nall passed")


if __name__ == "__main__":
    main()
