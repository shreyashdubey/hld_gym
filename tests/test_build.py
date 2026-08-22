#!/usr/bin/env python3
"""Assert-based checks for build.py and the deploy wiring. No pytest in this repo.

Run: python3 tests/test_build.py
"""
import json, re, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_publish_excludes_origins():
    """sell's publish:book runs rsync --delete. Without an origins exclude it
    deletes dist/origins/ wholesale on the next publish. Same trap the root
    AGENTS.md documents for book/ and reels/."""
    pkg = json.loads((ROOT / "sell" / "package.json").read_text())
    publish = pkg["scripts"]["publish:book"]
    assert "--delete" in publish, "publish:book no longer uses --delete; this test is stale"
    for d in ("book/", "reels/", "playground/", "origins/"):
        assert f"--exclude '{d}'" in publish, f"publish:book is missing --exclude '{d}'"


def test_vercel_has_origins_headers():
    cfg = json.loads((ROOT / "vercel.json").read_text())
    block = next((h for h in cfg["headers"] if h["source"] == "/origins/(.*)"), None)
    assert block, "vercel.json has no cache rule for /origins/"
    # not 'immutable': asset filenames are not content-hashed, so an immutable
    # rule would pin a stale image permanently
    values = {h["key"]: h["value"] for h in block["headers"]}
    assert values.get("Cache-Control") == "public, max-age=0, must-revalidate", \
        f"/origins/ Cache-Control is {values.get('Cache-Control')!r}"


def test_sitemap_lists_origins():
    sm = (ROOT / "sell" / "app" / "sitemap.ts").read_text()
    assert "/origins/" in sm, "sitemap.ts does not list /origins/"


def test_vercel_catchall_headers_stay_last():
    cfg = json.loads((ROOT / "vercel.json").read_text())
    assert cfg["headers"][-1]["source"] == "/(.*)", \
        "the catch-all security-header block must remain last in vercel.json"


def test_both_outputs_exist():
    """One build produces both views. The book keeps its own path and identity."""
    book = ROOT / "dist" / "book" / "index.html"
    origins = ROOT / "dist" / "origins" / "index.html"
    assert book.exists(), "dist/book/index.html missing — run python3 build.py"
    assert origins.exists(), "dist/origins/index.html missing"


def test_outputs_carry_distinct_modes():
    book = (ROOT / "dist" / "book" / "index.html").read_text()
    origins = (ROOT / "dist" / "origins" / "index.html").read_text()
    assert '<body data-mode="book">' in book, "book output has no data-mode=book"
    assert '<body data-mode="origins">' in origins, "origins output has no data-mode=origins"
    assert "hld-gym.vercel.app/book/" in book
    assert "hld-gym.vercel.app/origins/" in origins, "origins canonical still points at /book/"
    assert "/origins/" not in book.split("</head>")[0], "book <head> leaked an origins URL"


def test_no_unreplaced_placeholders():
    for p in ("dist/book/index.html", "dist/origins/index.html"):
        html = (ROOT / p).read_text()
        left = re.findall(r"\{\{[A-Z_]+\}\}", html)
        assert not left, f"{p} has unreplaced placeholders: {sorted(set(left))}"


def test_origin_fragment_reaches_origins_only():
    book = (ROOT / "dist" / "book" / "index.html").read_text()
    origins = (ROOT / "dist" / "origins" / "index.html").read_text()
    # match the emitted element, not the bare attribute: app.js ships in both
    # outputs and its `template[data-origin="..."]` selector is not a fragment
    assert '<template data-origin="p2c03">' in origins, "origin fragment missing from /origins"
    assert "<template data-origin" not in book, "origin fragment leaked into /book"


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
    img = '<p><img src="assets/lamport.webp" alt="Leslie Lamport in 1989"></p>'
    errs = _validate(img, "chapter")
    assert any("<img> forbidden" in e for e in errs), errs
    assert not _validate(img, "origin"), f"origin <img> wrongly rejected: {_validate(img, 'origin')}"


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


def test_cards_reach_origins_only():
    book = (ROOT / "dist" / "book" / "index.html").read_text()
    origins = (ROOT / "dist" / "origins" / "index.html").read_text()
    assert '"p2c03-c1"' in origins, "cards missing from /origins"
    assert '"p2c03-c1"' not in book, "cards leaked into /book"


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


def test_referenced_assets_reach_origins():
    """Was test_assets_copied_to_origins, which asserted that *every* file in
    src/assets/ ships - the assertion that put licences.json on the open
    internet. What must ship is what a card or an origin story points at."""
    src = ROOT / "src" / "assets"
    dst = ROOT / "dist" / "origins" / "assets"
    refs = set()
    for f in (ROOT / "src" / "chapters").iterdir():
        if f.name.endswith((".cards.json", ".origin.html")):
            refs |= set(re.findall(r'"assets/([^"]+)"', f.read_text()))
    refs = {r for r in refs if (src / r).is_file()}
    if not refs:
        return  # nothing wired up yet; the missing-asset test below is the real guard
    for r in sorted(refs):
        assert (dst / r).exists(), f"{r} is referenced but missing from dist/origins/assets/"


def test_missing_asset_is_a_build_error():
    sys.path.insert(0, str(ROOT))
    import build
    build.errors.clear()
    build.check_assets("ptest", '<p><img src="assets/does-not-exist.webp" alt="x"></p>')
    assert build.errors, "a reference to a nonexistent asset should fail the build"


def test_check_assets_rejects_path_traversal():
    """src="assets/../../build.py" passed both the prefix check and the
    existence check, then was never copied into dist/origins/assets/ - a
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
    dst = ROOT / "dist" / "origins" / "assets"
    if not dst.exists():
        return  # nothing built; test_both_outputs_exist is the guard for that
    stray = sorted(p.name for p in dst.rglob("*")
                   if p.is_file() and p.suffix.lower() not in build.IMAGE_EXTS)
    assert not stray, f"non-image working files reached dist/origins/assets/: {stray}"


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
