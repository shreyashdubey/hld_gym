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
