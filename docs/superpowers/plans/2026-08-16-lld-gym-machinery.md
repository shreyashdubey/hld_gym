# LLD Gym Machinery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `python3 build.py --book lld` produce a working LLD Gym at `dist/lld/index.html`, with executable code blocks, stdlib syntax highlighting, and one exemplar chapter that proves the whole pipeline.

**Architecture:** One build script serves two books via a `BOOKS` dict and a `--book` flag. Chapter HTML never contains code — it references real `.py` files that `build.py` executes and inlines. Highlighting uses Python's own `tokenize`, so no dependency is added and a syntax error fails the build. The engine (`template.html`, `style.css`, `app.js`) is shared unchanged between books except for a book id, a cross-link, and a boss-key namespace fix.

**Tech Stack:** Python 3.14 stdlib only (`tokenize`, `keyword`, `subprocess`, `html`, `io`, `re`, `json`, `pathlib`). Vanilla JS. No test framework — `unittest` from stdlib.

**Spec:** `docs/superpowers/specs/2026-08-16-lld-gym-design.md`

## Global Constraints

- **No new dependency in `build.py`.** It imports `base64, json, re, sys, pathlib` today. This plan adds only stdlib: `html, io, keyword, subprocess, tokenize`.
- **Argument parsing matches the file's existing crude style** (`"--check" in sys.argv`). Do not introduce `argparse`.
- **`python3 build.py` with no arguments must keep building HLD to `dist/book/index.html`.** Default book is `hld`. Any change that breaks the existing invocation is a failed task.
- **Book CSS scales via `rem`/`em`**, because `html { font-size: calc(16px * var(--fs,1)) }` at `src/style.css:99` already does the scaling. Never write `calc(Npx * var(--fs))` in `src/style.css` — that is the sprint's convention and would double-scale.
- **Both books share the `hldgym_v1` localStorage key.** Do not add a second key.
- **HLD boss records keep bare integer keys.** Namespacing them would orphan existing readers' data.
- **`--exclude 'lld/'` must be in `publish:book`** before or in the same commit as the first `dist/lld/` write.
- Design system holds: zero border-radius, 1px borders, colour only from `:root` tokens, mono for anything measured, lowercase chrome.
- Content language is Python. Types are load-bearing (`Protocol`, `ABC`, frozen dataclasses, enums).

---

### Task 1: Two books from one script

**Files:**
- Modify: `build.py:6-11` (paths), `build.py:81-120` (`main`)
- Modify: `src/template.html:6` (title), `src/template.html:37` (brand), `src/template.html:57` (book id script)
- Modify: `sell/package.json:9` (`publish:book`)
- Create: `src/lld/toc.json`
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `BOOKS: dict[str, dict]` with keys `chapters: Path`, `toc: Path`, `out: Path`, `title: str`, `mark: str`; `book_arg() -> str` returning the selected book id.

- [ ] **Step 1: Write the failing test**

Create `tests/test_build.py`:

```python
import subprocess, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import build


class TestBooks(unittest.TestCase):
    def test_default_book_is_hld(self):
        self.assertEqual(build.book_arg([]), "hld")

    def test_book_flag_selects_lld(self):
        self.assertEqual(build.book_arg(["--book", "lld"]), "lld")

    def test_unknown_book_raises(self):
        with self.assertRaises(SystemExit):
            build.book_arg(["--book", "nope"])

    def test_lld_writes_under_dist_lld(self):
        self.assertEqual(build.BOOKS["lld"]["out"].parent.name, "lld")
        self.assertEqual(build.BOOKS["hld"]["out"].parent.name, "book")


class TestExistingBuildStillWorks(unittest.TestCase):
    def test_hld_check_passes(self):
        p = subprocess.run([sys.executable, "build.py", "--check"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("51 chapters valid", p.stdout)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s tests -t . -v`
Expected: FAIL with `AttributeError: module 'build' has no attribute 'book_arg'`

- [ ] **Step 3: Write minimal implementation**

In `build.py`, replace the `OUT` constant block (lines 9-11) with:

```python
BOOKS = {
    "hld": {"chapters": SRC / "chapters", "toc": SRC / "toc.json",
            "out": ROOT / "dist" / "book" / "index.html",
            "title": "HLD Gym", "mark": "HLD"},
    "lld": {"chapters": SRC / "lld" / "chapters", "toc": SRC / "lld" / "toc.json",
            "out": ROOT / "dist" / "lld" / "index.html",
            "title": "LLD Gym", "mark": "LLD"},
}

def book_arg(argv):
    """--book <id>, defaulting to hld so the bare `python3 build.py` is unchanged."""
    if "--book" not in argv:
        return "hld"
    i = argv.index("--book")
    name = argv[i + 1] if i + 1 < len(argv) else ""
    if name not in BOOKS:
        sys.exit(f"unknown book {name!r}; expected one of {', '.join(BOOKS)}")
    return name
```

Rewrite `main()` to take the book from the flag. Replace the head of `main` and every use of `CH` and `OUT`:

```python
def main():
    check_only = "--check" in sys.argv
    book = book_arg(sys.argv)
    cfg = BOOKS[book]
    ch_dir = cfg["chapters"]
    toc = json.loads(cfg["toc"].read_text())
    templates, quiz_all = [], {}
    ready = 0
    for part in toc["parts"]:
        for ch in part["chapters"]:
            cid = ch["id"]
            h, qf = ch_dir / f"{cid}.html", ch_dir / f"{cid}.quiz.json"
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
        .replace("{{BOOK_TITLE}}", cfg["title"])
        .replace("{{BOOK_MARK}}", cfg["mark"])
        .replace("{{BOOK_ID}}", book)
        .replace("/*{{FONTS_CSS}}*/", font_css())
        .replace("/*{{STYLE_CSS}}*/", (SRC / "style.css").read_text())
        .replace("<!--{{CHAPTER_TEMPLATES}}-->", "\n".join(templates))
        .replace("/*{{TOC_JSON}}*/", json.dumps(toc).replace("</", "<\\/"))
        .replace("/*{{QUIZ_JSON}}*/", json.dumps(quiz_all).replace("</", "<\\/"))
        .replace("/*{{APP_JS}}*/", (SRC / "app.js").read_text().replace("</script", "<\\/script")))
    out = cfg["out"]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page)
    print(f"Built {out} ({out.stat().st_size / 1024:.0f} KB, {ready} chapters)")
```

Delete the now-unused `CH = SRC / "chapters"` line.

In `src/template.html`, make three edits:

```html
<title>{{BOOK_TITLE}}</title>
```

```html
<a class="brand" href="/"><span class="brand-mark">{{BOOK_MARK}}</span> Gym</a>
```

Immediately before `<script type="application/json" id="toc-data">`, add:

```html
<script>window.BOOK = "{{BOOK_ID}}";</script>
```

Create `src/lld/toc.json` with the five parts and 46 chapter ids from spec §"Content structure". Start with only `l2c01` present; the rest are entries whose files do not exist yet and therefore render as "coming soon", exactly as HLD did during authoring.

In `sell/package.json`, add the guard:

```json
"publish:book": "next build && rsync -a --delete --exclude 'book/' --exclude 'lld/' --exclude 'reels/' out/ ../dist/",
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -t . -v`
Expected: PASS, 5 tests.

Run: `python3 build.py && python3 build.py --book lld`
Expected: `Built .../dist/book/index.html (… 51 chapters)` then `Built .../dist/lld/index.html (… 0 chapters)`

- [ ] **Step 5: Commit**

```bash
git add build.py src/template.html src/lld/toc.json sell/package.json tests/test_build.py
git commit -m "build: serve two books from one script, add the lld rsync guard"
```

---

### Task 2: Syntax highlighting from the standard library

**Files:**
- Modify: `build.py` (imports, new `highlight`)
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: nothing from Task 1.
- Produces: `highlight(src: str) -> str` returning HTML-escaped source with `<span class="tok-kw|tok-str|tok-num|tok-com|tok-op">` wrappers. Raises `tokenize.TokenError` or `IndentationError` on invalid Python.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_build.py`:

```python
import html as _html, re as _re, tokenize


def strip_tags(s):
    return _html.unescape(_re.sub(r"<[^>]+>", "", s))


class TestHighlight(unittest.TestCase):
    def test_keyword_is_wrapped(self):
        self.assertIn('<span class="tok-kw">def</span>', build.highlight("def f():\n    pass\n"))

    def test_string_and_number(self):
        out = build.highlight("x = 'hi'\ny = 42\n")
        self.assertIn('<span class="tok-str">&#x27;hi&#x27;</span>', out)
        self.assertIn('<span class="tok-num">42</span>', out)

    def test_comment(self):
        self.assertIn('<span class="tok-com"># note</span>', build.highlight("x = 1  # note\n"))

    def test_angle_brackets_are_escaped(self):
        self.assertIn("&lt;", build.highlight("x: list[int] = []\nif 1 < 2:\n    pass\n"))

    def test_roundtrip_preserves_source_exactly(self):
        src = (
            "from dataclasses import dataclass\n"
            "\n"
            "\n"
            "@dataclass(frozen=True)\n"
            "class Money:\n"
            "    paise: int  # never float\n"
            "\n"
            "    def __add__(self, other: 'Money') -> 'Money':\n"
            "        return Money(self.paise + other.paise)\n"
        )
        self.assertEqual(strip_tags(build.highlight(src)), src)

    def test_roundtrip_with_multiline_string(self):
        src = 'DOC = """line one\nline two\n"""\nx = 1\n'
        self.assertEqual(strip_tags(build.highlight(src)), src)

    def test_empty_source(self):
        self.assertEqual(build.highlight(""), "")

    def test_invalid_python_raises(self):
        with self.assertRaises((tokenize.TokenError, IndentationError, SyntaxError)):
            build.highlight("def broken(:\n")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s tests -t . -v`
Expected: FAIL with `AttributeError: module 'build' has no attribute 'highlight'`

- [ ] **Step 3: Write minimal implementation**

Change `build.py`'s import line to:

```python
import base64, html as _html, io, json, keyword, re, subprocess, sys, tokenize
```

Add after `font_css()`:

```python
# Highlighting uses CPython's own lexer rather than a regex or a dependency:
# it is correct by construction, it is stdlib, and a file that will not
# tokenize is a syntax error the build catches before the code is ever run.
_TOK_CLASS = {t: c for t, c in (
    (tokenize.STRING, "tok-str"),
    (tokenize.NUMBER, "tok-num"),
    (tokenize.COMMENT, "tok-com"),
    (tokenize.OP, "tok-op"),
    (getattr(tokenize, "FSTRING_START", None), "tok-str"),
    (getattr(tokenize, "FSTRING_MIDDLE", None), "tok-str"),
    (getattr(tokenize, "FSTRING_END", None), "tok-str"),
) if t is not None}

_SKIP = {tokenize.ENDMARKER, tokenize.NEWLINE, tokenize.NL,
         tokenize.INDENT, tokenize.DEDENT}


def _tok_class(tok):
    if tok.type == tokenize.NAME:
        return "tok-kw" if keyword.iskeyword(tok.string) else None
    return _TOK_CLASS.get(tok.type)


def highlight(src):
    """Escaped source with token spans. Whitespace is reproduced byte for byte:
       everything between two tokens is emitted verbatim, so indentation and
       blank lines survive. Tokens are split at newlines so that a multi-line
       string never leaves a span open across a line boundary — line wrapping
       in as_lines() depends on that."""
    lines = src.splitlines(keepends=True)
    out, row, col = [], 1, 0

    def gap(to_row, to_col):
        nonlocal row, col
        while row < to_row:
            out.append(_html.escape(lines[row - 1][col:]))
            row, col = row + 1, 0
        out.append(_html.escape(lines[row - 1][col:to_col]))
        col = to_col

    for tok in tokenize.generate_tokens(io.StringIO(src).readline):
        if tok.type in _SKIP:
            continue
        gap(*tok.start)
        cls = _tok_class(tok)
        parts = _html.escape(tok.string).split("\n")
        out.append("\n".join(
            f'<span class="{cls}">{p}</span>' if cls and p else p for p in parts))
        row, col = tok.end

    while row <= len(lines):
        out.append(_html.escape(lines[row - 1][col:]))
        row, col = row + 1, 0
    return "".join(out)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -t . -v`
Expected: PASS, 13 tests.

- [ ] **Step 5: Commit**

```bash
git add build.py tests/test_build.py
git commit -m "build: highlight Python with the stdlib tokenizer, no dependency"
```

---

### Task 3: Line wrapping and change marks

**Files:**
- Modify: `build.py` (new `parse_marks`, `as_lines`)
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `highlight(src) -> str` from Task 2.
- Produces: `parse_marks(spec: str | None) -> set[int]`; `as_lines(hl: str, marks: set[int]) -> str` wrapping each line in `<span class="ln">` or `<span class="ln mark">`, 1-indexed.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_build.py`:

```python
class TestMarks(unittest.TestCase):
    def test_parse_single_and_range(self):
        self.assertEqual(build.parse_marks("12,18-21"), {12, 18, 19, 20, 21})

    def test_parse_empty(self):
        self.assertEqual(build.parse_marks(None), set())
        self.assertEqual(build.parse_marks(""), set())

    def test_parse_tolerates_spaces(self):
        self.assertEqual(build.parse_marks(" 3 , 5 - 6 "), {3, 5, 6})

    def test_as_lines_wraps_every_line(self):
        out = build.as_lines("a\nb\nc", set())
        self.assertEqual(out.count('<span class="ln">'), 3)

    def test_as_lines_marks_the_named_line(self):
        out = build.as_lines("a\nb\nc", {2})
        self.assertIn('<span class="ln mark">b</span>', out)
        self.assertIn('<span class="ln">a</span>', out)

    def test_marked_multiline_string_keeps_spans_closed(self):
        hl = build.highlight('X = """one\ntwo\n"""\n')
        wrapped = build.as_lines(hl, {2})
        for line in wrapped.split("\n"):
            self.assertEqual(line.count("<span"), line.count("</span>"), line)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s tests -t . -v`
Expected: FAIL with `AttributeError: module 'build' has no attribute 'parse_marks'`

- [ ] **Step 3: Write minimal implementation**

Add to `build.py` after `highlight`:

```python
def parse_marks(spec):
    """'12,18-21' -> {12,18,19,20,21}. 1-indexed, inclusive ranges."""
    out = set()
    for part in (p.strip() for p in (spec or "").split(",")):
        if not part:
            continue
        if "-" in part:
            a, b = part.split("-", 1)
            out.update(range(int(a), int(b.strip()) + 1))
        else:
            out.add(int(part))
    return out


def as_lines(hl, marks):
    return "\n".join(
        f'<span class="ln{" mark" if i in marks else ""}">{line}</span>'
        for i, line in enumerate(hl.split("\n"), 1))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -t . -v`
Expected: PASS, 19 tests.

- [ ] **Step 5: Commit**

```bash
git add build.py tests/test_build.py
git commit -m "build: wrap code lines and mark the ones that changed"
```

---

### Task 4: Inline code files, and run them

**Files:**
- Modify: `build.py` (new `run_code_file`, `inline_code`; call site in `main`)
- Test: `tests/test_build.py`, fixtures under `tests/fixtures/`

**Interfaces:**
- Consumes: `highlight`, `parse_marks`, `as_lines`.
- Produces: `run_code_file(path: Path) -> str | None` (message on failure, `None` on success); `inline_code(cid: str, html: str, code_dir: Path) -> str` which replaces every `<figure class="code" data-src=… data-mark=…>` with the same figure containing a `<pre><code>` of the highlighted file, and calls `err()` for each problem.

- [ ] **Step 1: Write the failing test**

Create `tests/fixtures/ok.py`:

```python
def add(a: int, b: int) -> int:
    return a + b


if __name__ == "__main__":
    assert add(2, 2) == 4
    print("ok")
```

Create `tests/fixtures/fails.py`:

```python
if __name__ == "__main__":
    assert 1 == 2, "deliberately failing self-check"
```

Create `tests/fixtures/slow.py`:

```python
import time

if __name__ == "__main__":
    time.sleep(60)
```

Append to `tests/test_build.py`:

```python
FIX = ROOT / "tests" / "fixtures"


class TestRunCodeFile(unittest.TestCase):
    def test_passing_file_returns_none(self):
        self.assertIsNone(build.run_code_file(FIX / "ok.py"))

    def test_failing_file_returns_message(self):
        msg = build.run_code_file(FIX / "fails.py")
        self.assertIsNotNone(msg)
        self.assertIn("AssertionError", msg)

    def test_slow_file_times_out(self):
        msg = build.run_code_file(FIX / "slow.py", timeout=1)
        self.assertIn("timed out", msg)


class TestInlineCode(unittest.TestCase):
    def setUp(self):
        build.errors.clear()

    def test_inlines_highlighted_source_before_the_caption(self):
        frag = ('<figure class="code" data-src="ok.py">'
                '<figcaption>Adds.</figcaption></figure>')
        out = build.inline_code("t01", frag, FIX)
        self.assertIn('<span class="tok-kw">def</span>', out)
        self.assertLess(out.index("<pre>"), out.index("<figcaption>"))
        self.assertEqual(build.errors, [])

    def test_applies_data_mark(self):
        frag = ('<figure class="code" data-src="ok.py" data-mark="2">'
                '<figcaption>Adds.</figcaption></figure>')
        out = build.inline_code("t01", frag, FIX)
        self.assertIn('<span class="ln mark">', out)

    def test_missing_file_is_an_error(self):
        build.inline_code("t01", '<figure class="code" data-src="nope.py"></figure>', FIX)
        self.assertTrue(any("nope.py" in e for e in build.errors))

    def test_failing_selfcheck_is_an_error(self):
        build.inline_code("t01", '<figure class="code" data-src="fails.py"></figure>', FIX)
        self.assertTrue(any("fails.py" in e for e in build.errors))

    def test_chapter_without_code_is_untouched(self):
        frag = "<p>No code here.</p>"
        self.assertEqual(build.inline_code("t01", frag, FIX), frag)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s tests -t . -v`
Expected: FAIL with `AttributeError: module 'build' has no attribute 'run_code_file'`

- [ ] **Step 3: Write minimal implementation**

Add to `build.py` after `as_lines`:

```python
CODE_FIG = re.compile(r'<figure class="code"([^>]*)>', re.I)
ATTR = re.compile(r'data-(src|mark)="([^"]*)"')


def run_code_file(path, timeout=15):
    """Every code file ends in an assert-based __main__ self-check. A book whose
       snippets do not run is worse than a book with a wrong story, because the
       reader pastes them. cwd is the file's own directory so a chapter may split
       code across sibling modules."""
    try:
        p = subprocess.run([sys.executable, str(path)], cwd=path.parent,
                           capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return f"timed out after {timeout}s"
    if p.returncode != 0:
        tail = p.stderr.strip().splitlines()
        return tail[-1] if tail else f"exited {p.returncode}"
    return None


def inline_code(cid, html, code_dir):
    def sub(m):
        attrs = dict(ATTR.findall(m.group(1)))
        src = attrs.get("src")
        if not src:
            err(f"{cid}: <figure class=\"code\"> without data-src")
            return m.group(0)
        path = code_dir / src
        if not path.exists():
            err(f"{cid}: code file not found: {src}")
            return m.group(0)
        text = path.read_text()
        try:
            hl = highlight(text)
        except Exception as e:
            err(f"{cid}: {src} is not valid Python: {e}")
            return m.group(0)
        problem = run_code_file(path)
        if problem:
            err(f"{cid}: {src} self-check failed: {problem}")
            return m.group(0)
        body = as_lines(hl, parse_marks(attrs.get("mark")))
        return f'{m.group(0)}<pre><code>{body}</code></pre>'
    return CODE_FIG.sub(sub, html)
```

Wire it into `main()`, immediately after `validate_html(cid, html)` so validation still runs on authored source:

```python
            validate_html(cid, html)
            html = inline_code(cid, html, ch_dir / f"{cid}.code")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -t . -v`
Expected: PASS, 27 tests.

Run: `python3 build.py --check`
Expected: `OK: 51 chapters valid.` — HLD has no code figures, so it is unaffected.

- [ ] **Step 5: Commit**

```bash
git add build.py tests/
git commit -m "build: inline code files and fail the build when their self-checks do not pass"
```

---

### Task 5: Code in quiz stems

**Files:**
- Modify: `build.py:53-79` (`validate_quiz`)
- Modify: `src/app.js:243-249` (`renderQuizItem`)
- Modify: `src/style.css` (`.q-code`)
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `highlight` from Task 2.
- Produces: quiz items may carry an optional `"code"` string; `validate_quiz` replaces it with `"codeHtml"` (highlighted) in the returned items. Options remain plain text.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_build.py`:

```python
def _item(**over):
    item = {"id": "t01-q01", "level": 1, "type": "mcq", "tag": "x",
            "q": "Which principle does this class violate, and why?",
            "options": [{"t": "A", "correct": True, "why": "y" * 25},
                        {"t": "B", "correct": False, "why": "n" * 25},
                        {"t": "C", "correct": False, "why": "n" * 25}]}
    item.update(over)
    return item


class TestQuizCode(unittest.TestCase):
    def setUp(self):
        build.errors.clear()

    def test_code_becomes_codehtml(self):
        data = {"chapter": "t01", "items": [_item(code="x = 1\n")]}
        items = build.validate_quiz("t01", data)
        self.assertIn('<span class="tok-num">1</span>', items[0]["codeHtml"])
        self.assertNotIn("code", items[0])

    def test_item_without_code_is_unchanged(self):
        data = {"chapter": "t01", "items": [_item()]}
        items = build.validate_quiz("t01", data)
        self.assertNotIn("codeHtml", items[0])

    def test_invalid_code_is_an_error(self):
        data = {"chapter": "t01", "items": [_item(code="def broken(:\n")]}
        build.validate_quiz("t01", data)
        self.assertTrue(any("t01-q01" in e and "not valid Python" in e
                            for e in build.errors))
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s tests -t . -v -k QuizCode`
Expected: FAIL — `codeHtml` missing (`KeyError`).

- [ ] **Step 3: Write minimal implementation**

In `build.py`, inside `validate_quiz`'s `for q in items:` loop, after the `if len(q.get("q", "")) < 15:` check, add:

```python
        # Code in the stem only. Options stay plain text: renderQuizItem sets
        # textContent on the option button, and code inside a button is
        # unreadable anyway.
        if "code" in q:
            try:
                q["codeHtml"] = highlight(q.pop("code"))
            except Exception as e:
                err(f"{cid}:{qid}: quiz code is not valid Python: {e}")
```

Note: `validate_quiz` already ends with `return items`, and the level-count floors below this line are unchanged.

In `src/app.js`, in `renderQuizItem`, replace the `wrap.innerHTML = …` assignment and the line after it:

```js
  wrap.innerHTML = `<div class="q-num">${num || ''}${q.tag ? ' · ' + q.tag : ''} · level ${q.level}</div>
    ${q.codeHtml ? `<pre class="q-code"><code>${q.codeHtml}</code></pre>` : ''}
    <div class="q-text"></div>`;
  wrap.querySelector('.q-text').textContent = q.q;
```

`codeHtml` is generated by `build.py` from escaped source, so interpolating it is safe; the question text keeps `textContent`.

In `src/style.css`, beside the existing `.content pre` rule, add:

```css
/* A quiz stem that is code. Sits inside the question card, so it takes the
   recessed surface rather than the panel the prose blocks use. */
.q-code {
  background: var(--paper); border: 1px solid var(--line);
  padding: 10px 12px; margin: 0 0 10px; overflow-x: auto;
  font-size: .78rem; line-height: 1.6;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -t . -v`
Expected: PASS, 30 tests.

Run: `python3 build.py --check`
Expected: `OK: 51 chapters valid.`

- [ ] **Step 5: Commit**

```bash
git add build.py src/app.js src/style.css tests/test_build.py
git commit -m "quiz: allow a code stem, highlighted at build time"
```

---

### Task 6: The refactor block and token colours

**Files:**
- Modify: `build.py:16-17` (`ALLOWED_DIV`)
- Modify: `src/style.css` (token classes, `.ln`, `.refactor`, `figure.code`)
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: the `tok-*` and `ln` classes emitted by Tasks 2 and 3.
- Produces: `refactor` permitted in `ALLOWED_DIV`; CSS for `.tok-kw`, `.tok-str`, `.tok-num`, `.tok-com`, `.tok-op`, `.ln`, `.ln.mark`, `.refactor`, `figure.code`.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_build.py`:

```python
class TestRefactorClass(unittest.TestCase):
    def setUp(self):
        build.warnings.clear()

    def test_refactor_div_is_allowed(self):
        build.validate_html("t01", '<div class="refactor"><p>x</p></div>')
        self.assertEqual(build.warnings, [])

    def test_unknown_div_still_warns(self):
        build.validate_html("t01", '<div class="wat"><p>x</p></div>')
        self.assertTrue(any("wat" in w for w in build.warnings))


class TestTokenCss(unittest.TestCase):
    def test_every_emitted_class_is_styled(self):
        css = (ROOT / "src" / "style.css").read_text()
        for cls in ("tok-kw", "tok-str", "tok-num", "tok-com", "tok-op", "ln"):
            self.assertIn(f".{cls}", css, f"{cls} emitted by build.py but never styled")

    def test_code_css_uses_rem_not_the_sprint_fs_convention(self):
        css = (ROOT / "src" / "style.css").read_text()
        block = css[css.index("/* code blocks"):]
        self.assertNotIn("var(--fs)", block)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s tests -t . -v -k "Refactor or TokenCss"`
Expected: FAIL — `refactor` warns as unknown, and `style.css` has no `/* code blocks` section.

- [ ] **Step 3: Write minimal implementation**

In `build.py`, add `"refactor"` to `ALLOWED_DIV`:

```python
ALLOWED_DIV = {"box", "box-tag", "analogy", "story", "lens", "crux", "feynman", "fey-prompt",
               "fey-model", "exercise", "ex-q", "takeaways", "diagram", "refactor", "code"}
```

Append to `src/style.css`:

```css
/* code blocks ---------------------------------------------------------------
   Sizes are rem because html{} already multiplies by --fs (line 99). Writing
   calc(Npx * var(--fs)) here is the sprint's convention and would scale twice.
   Token colours are the existing status tokens, not new hues: the palette is
   closed and code is not a reason to open it. */
figure.code { margin: 1.4em 0; }
figure.code pre { margin: 0; }
figure.code figcaption {
  font-family: var(--font-mono); font-size: .72rem; color: var(--ink-3);
  margin-top: 6px;
}
.content pre code .ln { display: block; }
.content pre code .ln.mark {
  background: var(--accent-soft);
  box-shadow: -12px 0 0 var(--accent-soft), 2px 0 0 var(--accent-soft);
}
.tok-kw  { color: var(--accent-ink); font-weight: 600; }
.tok-str { color: var(--good); }
.tok-num { color: var(--warm); }
.tok-com { color: var(--ink-3); font-style: italic; }
.tok-op  { color: var(--ink-2); }

/* before and after, stacked. ponytail: side-by-side above 880px is the obvious
   upgrade, unbuilt because the phone column is where this book gets read and
   stacked is correct there. */
.refactor { display: grid; gap: 10px; margin: 1.4em 0; }
.refactor figure.code { margin: 0; }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -t . -v`
Expected: PASS, 34 tests.

- [ ] **Step 5: Commit**

```bash
git add build.py src/style.css tests/test_build.py
git commit -m "style: token colours, marked lines, and the refactor block"
```

---

### Task 7: Book id, cross-link, and the boss-key collision

**Files:**
- Modify: `src/app.js:11-30` (book const), `src/app.js:128-180` (`renderSidebar`), `src/app.js:346` (`renderHome` boss read), `src/app.js:783-822` (`renderBoss`)
- Modify: `src/style.css` (`.side-cross`)
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: `window.BOOK` set by `template.html` in Task 1.
- Produces: `BOOK` const in `app.js`; `bossKey(n) -> string`; a sidebar entry linking to the other book.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_build.py`:

```python
class TestBossNamespace(unittest.TestCase):
    def test_app_js_namespaces_boss_by_book(self):
        js = (ROOT / "src" / "app.js").read_text()
        self.assertIn("function bossKey(", js)
        self.assertNotIn("S.boss[part]", js)
        self.assertNotIn("S.boss[p.n]", js)

    def test_hld_boss_keys_stay_bare(self):
        """Namespacing HLD would orphan every existing reader's boss record."""
        js = (ROOT / "src" / "app.js").read_text()
        self.assertIn("BOOK === 'hld'", js)

    def test_template_exposes_the_book_id(self):
        tpl = (ROOT / "src" / "template.html").read_text()
        self.assertIn('window.BOOK = "{{BOOK_ID}}"', tpl)

    def test_both_books_build(self):
        for args in ([], ["--book", "lld"]):
            p = subprocess.run([sys.executable, "build.py", *args],
                               cwd=ROOT, capture_output=True, text=True)
            self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s tests -t . -v -k BossNamespace`
Expected: FAIL — `bossKey` is not defined in `app.js`.

- [ ] **Step 3: Write minimal implementation**

In `src/app.js`, after the `RANKS` const, add:

```js
/* Which book this build is. Set by template.html before this script runs. */
const BOOK = window.BOOK || 'hld';
const OTHER = BOOK === 'hld' ? { id: 'lld', href: '/lld/', name: 'low-level design' }
                             : { id: 'hld', href: '/book/', name: 'high-level design' };

/* Both books share hldgym_v1 — one streak, one xp pool, one rank — and chapter
   ids never collide. S.boss did collide: it was keyed by bare part number and
   both books have a Part 1, so lld would have overwritten hld's record. hld
   keeps bare keys because namespacing it would orphan every existing reader. */
const bossKey = n => BOOK === 'hld' ? String(n) : BOOK + n;
```

In `renderHome`, change the boss read:

```js
    const boss = S.boss[bossKey(p.n)];
```

In `renderBoss`, change the three uses:

```js
  const best = S.boss[bossKey(part)]?.best;
```

```js
        const rec = S.boss[bossKey(part)] = S.boss[bossKey(part)] || {};
```

In `renderSidebar`, extend the home block to carry the cross-link:

```js
  let html = `<a class="side-ch side-home${atHome ? ' active' : ''}" href="#home">
    <span class="n">◆</span><span>home</span></a>
    <a class="side-ch side-cross" href="${OTHER.href}">
    <span class="n">${OTHER.id === 'lld' ? '◇' : '◆'}</span><span>${OTHER.name}</span></a>`;
```

In `src/style.css`, beside the existing `.side-home` rule:

```css
.side-cross { color: var(--ink-3); }
.side-cross:hover { color: var(--accent-ink); }
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -t . -v`
Expected: PASS, 38 tests.

Manual check: `python3 -m http.server 8080 --directory dist`, open `localhost:8080/book/`, confirm the sidebar shows `home` then `low-level design`, and that the link reaches `/lld/`.

- [ ] **Step 5: Commit**

```bash
git add src/app.js src/style.css tests/test_build.py
git commit -m "engine: expose the book id, cross-link the two books, fix the boss-key collision"
```

---

### Task 8: The exemplar chapter, and the author contract

**Files:**
- Create: `src/lld/chapters/l2c01.html`
- Create: `src/lld/chapters/l2c01.quiz.json`
- Create: `src/lld/chapters/l2c01.code/pricing_v1.py`, `pricing_v3.py`, `pricing_after.py`
- Create: `STYLE_GUIDE-LLD.md`
- Test: `tests/test_build.py`

**Interfaces:**
- Consumes: everything from Tasks 1-7.
- Produces: a chapter that exercises the whole pipeline — three code files, a `.refactor` block, a quiz with a code stem, the third-change rule, and a stated price.

- [ ] **Step 1: Write the failing test**

Append to `tests/test_build.py`:

```python
class TestExemplar(unittest.TestCase):
    def test_lld_builds_with_one_chapter(self):
        p = subprocess.run([sys.executable, "build.py", "--book", "lld", "--check"],
                           cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("OK: 1 chapters valid", p.stdout)

    def test_exemplar_states_the_price_of_the_abstraction(self):
        html = (ROOT / "src/lld/chapters/l2c01.html").read_text()
        self.assertIn("what it cost", html.lower())

    def test_exemplar_shows_three_changes_before_the_pattern(self):
        """The third-change rule is the book's spine and its hardest gate."""
        html = (ROOT / "src/lld/chapters/l2c01.html").read_text().lower()
        for n in ("change one", "change two", "change three"):
            self.assertIn(n, html)
        self.assertLess(html.index("change three"), html.index("strategy"))

    def test_every_code_file_has_a_selfcheck(self):
        for f in (ROOT / "src/lld/chapters/l2c01.code").glob("*.py"):
            self.assertIn('if __name__ == "__main__":', f.read_text(), f.name)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest discover -s tests -t . -v -k Exemplar`
Expected: FAIL with `FileNotFoundError` — `src/lld/chapters/l2c01.html` does not exist.

- [ ] **Step 3: Write minimal implementation**

Create `src/lld/chapters/l2c01.code/pricing_v1.py` — the code that shipped and is fine:

```python
"""Ride pricing, first version. One fare type, and it is correct."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Ride:
    km: float
    minutes: int


def fare_paise(ride: Ride) -> int:
    return round(4000 + ride.km * 1200 + ride.minutes * 150)


if __name__ == "__main__":
    assert fare_paise(Ride(km=0, minutes=0)) == 4000
    assert fare_paise(Ride(km=5, minutes=20)) == 13000
    print("ok")
```

Create `src/lld/chapters/l2c01.code/pricing_v3.py` — after three changes, the shape of the pain:

```python
"""Third change in. Still correct, and now every new fare type edits this
   function, the validator, and the receipt renderer."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Ride:
    km: float
    minutes: int
    kind: str


def fare_paise(ride: Ride) -> int:
    if ride.kind == "standard":
        return round(4000 + ride.km * 1200 + ride.minutes * 150)
    if ride.kind == "pool":
        return round(3000 + ride.km * 900 + ride.minutes * 120)
    if ride.kind == "rental":
        return round(50000 + max(0, ride.km - 40) * 1500)
    if ride.kind == "airport":
        return round(4000 + ride.km * 1200 + ride.minutes * 150) + 15000
    raise ValueError(f"unknown ride kind: {ride.kind}")


if __name__ == "__main__":
    assert fare_paise(Ride(5, 20, "standard")) == 13000
    assert fare_paise(Ride(5, 20, "pool")) == 9900
    assert fare_paise(Ride(50, 0, "rental")) == 65000
    assert fare_paise(Ride(5, 20, "airport")) == 28000
    print("ok")
```

Create `src/lld/chapters/l2c01.code/pricing_after.py` — the axis, made explicit:

```python
"""The axis the three changes revealed: a fare is a rule, and rules vary.
   Each rule now lives with the thing it prices, and adding one touches
   nothing that already works."""
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Ride:
    km: float
    minutes: int


class FareRule(Protocol):
    name: str

    def paise(self, ride: Ride) -> int: ...


@dataclass(frozen=True)
class PerKmAndMinute:
    name: str
    base: int
    per_km: int
    per_minute: int

    def paise(self, ride: Ride) -> int:
        return round(self.base + ride.km * self.per_km
                     + ride.minutes * self.per_minute)


@dataclass(frozen=True)
class Surcharged:
    inner: FareRule
    extra: int

    @property
    def name(self) -> str:
        return f"{self.inner.name}+surcharge"

    def paise(self, ride: Ride) -> int:
        return self.inner.paise(ride) + self.extra


@dataclass(frozen=True)
class IncludedKm:
    name: str
    flat: int
    included_km: float
    per_extra_km: int

    def paise(self, ride: Ride) -> int:
        return round(self.flat
                     + max(0.0, ride.km - self.included_km) * self.per_extra_km)


STANDARD = PerKmAndMinute("standard", 4000, 1200, 150)
POOL = PerKmAndMinute("pool", 3000, 900, 120)
RENTAL = IncludedKm("rental", 50000, 40.0, 1500)
AIRPORT = Surcharged(STANDARD, 15000)


def fare_paise(ride: Ride, rule: FareRule) -> int:
    return rule.paise(ride)


if __name__ == "__main__":
    assert fare_paise(Ride(5, 20), STANDARD) == 13000
    assert fare_paise(Ride(5, 20), POOL) == 9900
    assert fare_paise(Ride(50, 0), RENTAL) == 65000
    assert fare_paise(Ride(5, 20), AIRPORT) == 28000
    # the fourth change, which the old shape could not absorb without an edit
    night = Surcharged(POOL, 2500)
    assert fare_paise(Ride(5, 20), night) == 12400
    assert night.name == "pool+surcharge"
    print("ok")
```

Write `src/lld/chapters/l2c01.html` following `STYLE_GUIDE-LLD.md` and spec §"Chapter anatomy". Required structure, in order: cold open on `pricing_v1.py`; a section per change headed **Change one**, **Change two**, **Change three**; a section naming the pain; a `<div class="refactor">` holding `pricing_v3.py` and `pricing_after.py` as two `<figure class="code">` blocks with `data-mark` on the lines that moved; a section headed **What it cost**; `.lens`; `.feynman` with `data-key="l2c01-f1"`; three `.exercise` blocks where the last asks for a fourth fare type; `.takeaways`. 2500-4500 words. No `<h1>`. No inline `style=`. No external URLs.

Write `src/lld/chapters/l2c01.quiz.json` with 24-28 items at the 8-10 / 8-10 / 6-8 level split, every option carrying a `why` of 20+ characters, at least three items using the `"code"` stem field, and at least one level-3 item whose wrong options are over-engineering — a pattern introduced after one change.

Write `STYLE_GUIDE-LLD.md` carrying: the voice rules inherited from `STYLE_GUIDE.md` §1; the code-file convention (`<id>.code/`, `data-src`, `data-mark`, mandatory `__main__` self-check); the third-change rule as a hard gate; the price rule; the Python conventions (`Protocol`/`ABC`, frozen dataclasses, integer paise never floats for money, exhaustive `match`); the component list including `refactor` and `figure.code`; the quiz schema with the `code` field; and the statement that these rounds mostly run in Java and what transfers is the decomposition.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python3 -m unittest discover -s tests -t . -v`
Expected: PASS, 42 tests.

Run: `python3 build.py --book lld`
Expected: `OK: 1 chapters valid.` then `Built .../dist/lld/index.html`

Manual check: `python3 -m http.server 8080 --directory dist`, open `localhost:8080/lld/#ch/l2c01` in all three themes and at 390px. Confirm code is highlighted, marked lines are tinted, the refactor block stacks, the quiz code stem renders, and nothing scrolls sideways.

- [ ] **Step 5: Commit**

```bash
git add src/lld STYLE_GUIDE-LLD.md tests/test_build.py
git commit -m "lld: exemplar chapter l2c01 and the author contract"
```

---

## Self-review

**Spec coverage.** Every machinery requirement in spec §"Machinery", §"Build validation" and §"Routes, links, and state" maps to a task: code execution and inlining → Task 4; `tokenize` highlighting → Task 2; quiz `code` field → Task 5; refactor display → Tasks 6 and 8; `--book` → Task 1; `ALLOWED_DIV` → Task 6; the rsync guard → Task 1; the link graph and `S.boss` fix → Task 7; the exemplar and `STYLE_GUIDE-LLD.md` → Task 8.

**Deliberately out of this plan.** The 45 remaining chapters (a separate content plan, and a pipeline run rather than a task list); the sell page's second book link, which touches the concurrently-edited `sell/` tree and should land once that settles; side-by-side refactor view, marked `ponytail:` in Task 6.

**Known gap.** Spec §"Authoring and verification" describes three verifier gates. Task 8 pins two of them mechanically for the exemplar only (`test_exemplar_shows_three_changes_before_the_pattern`, `test_exemplar_states_the_price_of_the_abstraction`). Applying them across 46 chapters is the content plan's job, and those two tests are the template for it.
