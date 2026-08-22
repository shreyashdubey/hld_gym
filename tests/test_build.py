#!/usr/bin/env python3
"""Assert-based checks for build.py and the deploy wiring. No pytest in this repo.

Run: python3 tests/test_build.py
"""
import json, re, sys
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
    assert 'data-origin="p2c03"' in origins, "origin fragment missing from /origins"
    assert 'data-origin="' not in book, "origin fragment leaked into /book"


def _validate(html, kind):
    """Drive build.py's validator directly. It accumulates into a module global,
    so reset it around each call."""
    sys.path.insert(0, str(ROOT))
    import build
    build.errors.clear()
    build.validate_html("ptest", html, kind)
    return list(build.errors)


def test_img_rejected_in_chapter_allowed_in_origin():
    img = '<p><img src="assets/lamport.webp" alt="Leslie Lamport in 1989"></p>'
    assert _validate(img, "chapter"), "chapter fragments must still reject <img>"
    assert not _validate(img, "origin"), f"origin <img> wrongly rejected: {_validate(img, 'origin')}"


def test_origin_img_must_be_relative_and_described():
    external = '<p><img src="https://example.com/x.jpg" alt="x"></p>'
    assert _validate(external, "origin"), "external img src must be rejected"
    bare = '<p><img src="/other/x.webp" alt="x"></p>'
    assert _validate(bare, "origin"), "img src outside assets/ must be rejected"
    noalt = '<p><img src="assets/x.webp"></p>'
    assert _validate(noalt, "origin"), "img without alt must be rejected"


def test_event_handler_attributes_rejected_everywhere():
    """build.py has no attribute allowlist at all. Allowing <img> without this
    check would make an author typo an injection."""
    for kind in ("chapter", "origin"):
        assert _validate('<p onclick="alert(1)">x</p>', kind), f"on*= not caught in {kind}"


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
