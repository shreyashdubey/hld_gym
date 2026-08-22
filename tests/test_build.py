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
