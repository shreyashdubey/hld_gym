# Diagnostic Round Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A third voice-service mode, `diagnostic`: a ~6-minute interviewer-only round that ends in a written failure map (verbatim quotes + gaps + free-chapter links + one buy CTA) instead of a coach walkthrough.

**Architecture:** The existing Playground pipeline (`playground/pipelines.py`) is reused with a `kind` switch on `Session`; a new `playground/grading.py` runs one post-round LLM call whose output is schema- and substring-checked in code; the map travels over the existing RTVI app-message channel to `sell/app/playground/page.tsx`, which renders it via a new `FailureMap` component. Local only — no hosting, no sell-page CTA, no rsync-exclude change.

**Tech Stack:** Python 3.11, FastAPI, pipecat-ai 1.7.0, openai SDK (already installed via `pipecat-ai[openai]`), unittest; Next.js 16 static export, TypeScript, node:test.

**Spec:** `docs/superpowers/specs/2026-08-23-diagnostic-round-design.md`

## Global Constraints

- All commands run from the repo root (`/home/don/Desktop/misc-projects/jassi-shreyash`) unless a `cd` is shown.
- Python tests: `playground/.venv/bin/python -m unittest playground.tests.<module> -v` (the venv exists; `playground/tests/__init__.py` sets the token secret so imports work on a fresh clone).
- Sell tests: `cd sell && npm test` (runs `lib/*.test.ts` under node:test only — components are verified by lint + build + browser, per existing convention).
- **No em dashes (`—`) in any string that renders in the sell UI** — `grep -c '—' dist/index.html` must print 0 is a checked repo rule, and a UI string travels. Use plain words or `·`.
- **The interviewer never holds the answer key during a round.** `rep.KERNEL` / `rep.RUBRIC_LABELS` / `rep.PROBES` may enter only the grading pass, post-round.
- A diagnostic session never gets `draw_diagram` and never becomes a coach.
- Quotes in the failure map must be verbatim substrings of the transcript, checked in code; failures are dropped, never rendered.
- `mode=diagnostic` is auth-gated exactly like `mode=playground` (it spends OpenAI money per minute). `mode=dictation` stays open.
- Commit messages: plain sentences (repo style, no `feat:` prefixes), each ending with
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- **Do not touch** `sell/package.json`'s `publish:book` excludes, `dist/`, or any hosting/env concern — the spec defers all of it behind "the hosting gate".
- The working tree already carries unrelated uncommitted changes (`playground/*.py`, `playground/tests/*`, `sell/*`, `dist/sitemap.xml`). **Stage only the files each task names** — never `git add -A` or `git add .`.

---

### Task 1: Config knob `diagnostic_cap_secs`

**Files:**
- Modify: `playground/config.py` (dataclass fields, around line 24)
- Test: `playground/tests/test_config.py`

**Interfaces:**
- Consumes: nothing new.
- Produces: `VoiceConfig.diagnostic_cap_secs: float` (default `360.0`), env-overridable as `PLAYGROUND_DIAGNOSTIC_CAP_SECS` via the existing `from_env()` loop (float fields are parsed automatically — no `from_env` change needed).

- [ ] **Step 1: Write the failing tests**

Append to the config-defaults test class in `playground/tests/test_config.py` (read the file first; match its existing class and naming style):

```python
def test_diagnostic_cap_defaults_to_six_minutes(self):
    self.assertEqual(VoiceConfig().diagnostic_cap_secs, 360.0)

def test_diagnostic_cap_is_env_overridable(self):
    config = VoiceConfig.from_env({"PLAYGROUND_DIAGNOSTIC_CAP_SECS": "120"})
    self.assertEqual(config.diagnostic_cap_secs, 120.0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_config -v`
Expected: FAIL / ERROR with `TypeError` or `AttributeError` on `diagnostic_cap_secs`.

- [ ] **Step 3: Implement**

In `playground/config.py`, directly under the `session_cap_secs` field:

```python
    # The free diagnostic round is interviewer-only and shorter: it exists to
    # produce a failure map, not a walkthrough. Announced up front, same rule.
    diagnostic_cap_secs: float = 6 * 60
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_config -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add playground/config.py playground/tests/test_config.py
git commit -m "Add the diagnostic round's own session cap knob

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 2: `Session` kinds — diagnostic never coaches, uses its own cap

**Files:**
- Modify: `playground/session.py` (`__init__`, `switch_to_coach`, `system_messages`, `remaining_secs`)
- Test: `playground/tests/test_session.py`, `playground/tests/test_cap.py`

**Interfaces:**
- Consumes: `VoiceConfig.diagnostic_cap_secs` (Task 1). This task does NOT touch the persona pick — a diagnostic session still gets `interviewer_prompt()` here; Task 3 swaps in `diagnostic_prompt()`. Each task stays independently green.
- Produces, relied on by later tasks:
  - `Session(config, kind="sprint")` — `kind: str`, `"sprint"` or `"diagnostic"`.
  - `Session.kind: str`
  - `Session.cap_secs: float` — the cap this session actually runs under; `remaining_secs`/`expired` derive from it.
  - `Session.round_over: bool` — `False` at init; set by the server's end path (Task 7). Session only stores it.
  - `Session.closing: bool` — `False` at init; when `True` on a diagnostic session, `system_messages()` appends the time-is-up instruction.
  - `Session.switch_to_coach()` raises `RuntimeError` when `kind == "diagnostic"`.

- [ ] **Step 1: Write the failing tests**

Append to `playground/tests/test_session.py` (read it first; reuse its existing `_FakeContext`-style helpers if present, match style):

```python
class TestDiagnosticKind(unittest.TestCase):
    def setUp(self):
        self.s = Session(VoiceConfig(diagnostic_cap_secs=120), kind="diagnostic")

    def test_default_kind_is_sprint(self):
        self.assertEqual(Session(VoiceConfig()).kind, "sprint")

    def test_a_diagnostic_session_has_no_coach(self):
        # The free round withholds the walkthrough by design; a diagnostic
        # session that could become a coach would hand out the paid product.
        with self.assertRaises(RuntimeError):
            self.s.switch_to_coach()

    def test_a_diagnostic_session_never_offers_draw_diagram(self):
        names = [t.name for t in self.s.tools().standard_tools]
        self.assertEqual(names, ["end_round"])

    def test_round_over_and_closing_start_false(self):
        self.assertFalse(self.s.round_over)
        self.assertFalse(self.s.closing)

    def test_closing_appends_the_time_is_up_instruction(self):
        self.s.closing = True
        contents = [m["content"] for m in self.s.system_messages()]
        self.assertTrue(any("call end_round" in c for c in contents))

    def test_closing_is_ignored_for_a_sprint_session(self):
        sprint = Session(VoiceConfig())
        sprint.closing = True
        contents = [m["content"] for m in sprint.system_messages()]
        self.assertFalse(any("call end_round" in c for c in contents))
```

Append to `playground/tests/test_cap.py`:

```python
class TestDiagnosticCap(unittest.TestCase):
    def test_a_diagnostic_session_runs_under_its_own_cap(self):
        s = Session(VoiceConfig(session_cap_secs=600, diagnostic_cap_secs=120), kind="diagnostic")
        s.start(now=1000.0)
        self.assertEqual(s.remaining_secs(now=1000.0), 120)
        self.assertTrue(s.expired(now=1120.0))

    def test_a_sprint_session_still_runs_under_the_session_cap(self):
        s = Session(VoiceConfig(session_cap_secs=600, diagnostic_cap_secs=120))
        s.start(now=1000.0)
        self.assertEqual(s.remaining_secs(now=1000.0), 600)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_session playground.tests.test_cap -v`
Expected: FAIL/ERROR — `Session.__init__() got an unexpected keyword argument 'kind'`.

- [ ] **Step 3: Implement**

In `playground/session.py`:

`__init__` becomes:

```python
    def __init__(self, config: VoiceConfig, kind: str = "sprint") -> None:
        self.config = config
        # "sprint" is today's interviewer->coach session; "diagnostic" is the
        # free round: interviewer only, its own shorter cap, and it ends in a
        # written failure map instead of a walkthrough (see the 2026-08-23
        # spec). The kind never changes after construction.
        self.kind = kind
        self.cap_secs = config.diagnostic_cap_secs if kind == "diagnostic" else config.session_cap_secs
        self.mode = "interview"
        # Set by the server's end path exactly once; guards the three end
        # triggers (end_round, the finish click, the cap) from racing a
        # second grading pass. Session only stores it.
        self.round_over = False
        # When True on a diagnostic session, system_messages() tells the
        # interviewer time is up -- the cap's announced closing turn.
        self.closing = False
        self.board = BoardContext()
        self.context = None
        self.tts = None
        self._started_at: float | None = None
```

(Keep the existing comments on `context` and `tts` — the block above elides them for brevity; do not delete them in the real edit.)

`switch_to_coach` becomes:

```python
    def switch_to_coach(self) -> None:
        if self.kind == "diagnostic":
            # The free round withholds the walkthrough by design -- the coach
            # is what $19 buys. Structural, not conventional: a diagnostic
            # session that could switch would also pick up draw_diagram and
            # the answer key through tools()/system_messages().
            raise RuntimeError("a diagnostic session has no coach")
        self.mode = "coach"
```

In `remaining_secs`, replace both uses of `self.config.session_cap_secs` with `self.cap_secs` (the docstring's mention stays accurate for sprint; extend it with one line: "Diagnostic sessions run under config.diagnostic_cap_secs via self.cap_secs.").

In `system_messages`, after the `summary` block, before `return messages`:

```python
        if self.kind == "diagnostic" and self.closing:
            messages.append({
                "role": "system",
                "content": (
                    "Time is up. Say one closing sentence -- thank them, no "
                    "teaching, no verdict -- then call end_round."
                ),
            })
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_session playground.tests.test_cap -v`
Expected: all PASS (including the pre-existing tests — `Session(config)` callers are unaffected by the added default).

- [ ] **Step 5: Run the whole playground suite** (Session is imported widely)

Run: `playground/.venv/bin/python -m unittest discover -s playground/tests -t .`
Expected: OK, same count as before plus the new tests.

- [ ] **Step 6: Commit**

```bash
git add playground/session.py playground/tests/test_session.py playground/tests/test_cap.py
git commit -m "Give Session a kind: the diagnostic round has its own cap and no coach

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: Diagnostic interviewer persona

**Files:**
- Modify: `playground/personas.py`, `playground/session.py:99` (the persona pick in `system_messages`)
- Test: `playground/tests/test_personas.py`

**Interfaces:**
- Consumes: `Session.kind` (Task 2).
- Produces: `personas.diagnostic_prompt() -> str` — interviewer prompt for the free round. `Session.system_messages()` uses it when `kind == "diagnostic"` and `mode` is not coach.

- [ ] **Step 1: Write the failing tests**

Read `playground/tests/test_personas.py` first — it already asserts the interviewer prompt is starved of the answer key; mirror that exact technique. Append:

```python
class TestDiagnosticPrompt(unittest.TestCase):
    def test_the_diagnostic_interviewer_is_starved_of_the_answer_key(self):
        # Same invariant as the sprint interviewer: a model holding the
        # answers leaks them the moment a candidate sounds stuck, and then
        # the round graded nothing.
        prompt = diagnostic_prompt()
        self.assertNotIn(rep.KERNEL, prompt)
        for label in rep.RUBRIC_LABELS:
            self.assertNotIn(label, prompt)
        for probe in rep.PROBES:
            self.assertNotIn(probe["a"], prompt)

    def test_it_still_names_the_rep_and_end_round(self):
        prompt = diagnostic_prompt()
        self.assertIn(rep.REP_TITLE, prompt)
        self.assertIn("end_round", prompt)

    def test_a_diagnostic_session_uses_the_diagnostic_prompt(self):
        s = Session(VoiceConfig(), kind="diagnostic")
        self.assertIn(diagnostic_prompt(), s.system_messages()[0]["content"])
```

Add the imports the file is missing (`from playground.personas import diagnostic_prompt`, `from playground.session import Session`, `from playground.config import VoiceConfig` — check what it already imports).

- [ ] **Step 2: Run tests to verify they fail**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_personas -v`
Expected: ImportError on `diagnostic_prompt`.

- [ ] **Step 3: Implement**

In `playground/personas.py`, after `_INTERVIEWER`:

```python
_DIAGNOSTIC = f"""{_SHARED}

You are a senior interviewer running one short diagnostic round on:
{rep.REP_TITLE}. The candidate gets about six minutes.

Run it tight. Push where they hand-wave: ask for numbers when they gesture at
scale, ask what breaks when they claim something works, make them defend a
choice rather than agreeing with it. Move on once a gap is exposed -- the
round exists to find gaps, not to dwell on one.

You do not know the model answer and you do not hint. You never teach and you
never give a verdict out loud; a written report follows the round. When the
round has shown what it is going to show, or the candidate says they are
done, call end_round with a one-line reason.
"""
```

And:

```python
def diagnostic_prompt() -> str:
    return _DIAGNOSTIC
```

In `playground/session.py`, `system_messages()` line 99 becomes:

```python
        if self.mode == "coach":
            persona = coach_prompt()
        elif self.kind == "diagnostic":
            persona = diagnostic_prompt()
        else:
            persona = interviewer_prompt()
```

(and extend the import at the top: `from playground.personas import coach_prompt, diagnostic_prompt, interviewer_prompt`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_personas playground.tests.test_session -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add playground/personas.py playground/session.py playground/tests/test_personas.py
git commit -m "Add the diagnostic interviewer persona, starved of the answer key like the sprint one

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: Grading core — prompt build, parse, verbatim check, gap→chapter table

**Files:**
- Create: `playground/grading.py`
- Test: `playground/tests/test_grading.py` (new)

**Interfaces:**
- Consumes: `rep.KERNEL`, `rep.RUBRIC_LABELS`, `rep.PROBES` (existing).
- Produces (Task 5 and Task 7 rely on these exact names):
  - `GAP_CHAPTERS: dict[str, str]` — gap-area key → free-book URL.
  - `transcript_text(turns: list) -> str` — the candidate's words only.
  - `build_grading_messages(turns: list, board_text: str) -> list[dict]` — the LLM messages for the grading call.
  - `parse_and_check(raw: str, transcript: str) -> list[dict] | None` — `None` = unparseable; otherwise 0–3 moments, each `{"quote", "probe", "gap", "chapter"}` with `chapter` already resolved to a URL.

- [ ] **Step 1: Write the failing tests**

Create `playground/tests/test_grading.py`:

```python
import unittest

from playground import rep
from playground.grading import (
    GAP_CHAPTERS,
    build_grading_messages,
    parse_and_check,
    transcript_text,
)

TURNS = [
    {"role": "system", "content": "persona"},
    {"role": "user", "content": "we'll just shard it"},
    {"role": "assistant", "content": "What's the shard key?"},
    {"role": "user", "content": [{"type": "text", "text": "the cache goes and fetches it"}]},
]


class TestTranscriptText(unittest.TestCase):
    def test_user_turns_only_in_order(self):
        self.assertEqual(
            transcript_text(TURNS),
            "we'll just shard it\nthe cache goes and fetches it",
        )

    def test_tolerates_junk_shapes(self):
        # Turns come out of a live LLMContext; content can be a string, a
        # parts list, or absent. None of those may crash a grading pass.
        junk = [{"role": "user"}, "not a dict", {"role": "user", "content": [{"no": "text"}]}]
        self.assertEqual(transcript_text(junk), "")


class TestGradingMessages(unittest.TestCase):
    # The one place the answer key is allowed to appear: after the round.
    def test_the_grader_holds_the_answer_key(self):
        text = str(build_grading_messages(TURNS, "Components: App, Cache"))
        self.assertIn(rep.KERNEL, text)
        for label in rep.RUBRIC_LABELS:
            self.assertIn(label, text)

    def test_the_grader_sees_transcript_and_board(self):
        text = str(build_grading_messages(TURNS, "Components: App, Cache"))
        self.assertIn("we'll just shard it", text)
        self.assertIn("Components: App, Cache", text)

    def test_every_gap_area_is_offered_to_the_model(self):
        text = str(build_grading_messages(TURNS, ""))
        for key in GAP_CHAPTERS:
            self.assertIn(key, text)


class TestParseAndCheck(unittest.TestCase):
    TRANSCRIPT = "we'll just shard it\nthe cache goes and fetches it"

    def _moment(self, **over):
        m = {
            "quote": "we'll just shard it",
            "probe": "what the shard key is",
            "gap": "no shard key named",
            "gap_area": "cache_aside_vs_read_through",
        }
        m.update(over)
        return m

    def test_a_verbatim_quote_survives_with_its_chapter_resolved(self):
        got = parse_and_check('{"moments": [%s]}' % __import__("json").dumps(self._moment()), self.TRANSCRIPT)
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["chapter"], GAP_CHAPTERS["cache_aside_vs_read_through"])
        self.assertNotIn("gap_area", got[0])

    def test_a_fabricated_quote_is_dropped_not_rendered(self):
        # An invented quote on a sales surface is the standing honesty rule
        # broken in the worst place: in the visitor's own mouth.
        import json
        raw = json.dumps({"moments": [self._moment(quote="I have no idea")]})
        self.assertEqual(parse_and_check(raw, self.TRANSCRIPT), [])

    def test_an_unknown_gap_area_is_dropped_the_model_does_not_mint_urls(self):
        import json
        raw = json.dumps({"moments": [self._moment(gap_area="blockchain")]})
        self.assertEqual(parse_and_check(raw, self.TRANSCRIPT), [])

    def test_at_most_three_moments(self):
        import json
        raw = json.dumps({"moments": [self._moment()] * 5})
        self.assertEqual(len(parse_and_check(raw, self.TRANSCRIPT)), 3)

    def test_zero_surviving_moments_is_a_valid_empty_map_not_a_failure(self):
        self.assertEqual(parse_and_check('{"moments": []}', self.TRANSCRIPT), [])

    def test_unparseable_json_is_none(self):
        self.assertIsNone(parse_and_check("the model rambled", self.TRANSCRIPT))

    def test_wrong_shapes_are_none_or_dropped(self):
        self.assertIsNone(parse_and_check('{"nope": 1}', self.TRANSCRIPT))
        self.assertIsNone(parse_and_check('{"moments": "x"}', self.TRANSCRIPT))
        self.assertEqual(parse_and_check('{"moments": [42, {"quote": ""}]}', self.TRANSCRIPT), [])


class TestGapChapters(unittest.TestCase):
    def test_every_chapter_link_points_into_the_free_book(self):
        for url in GAP_CHAPTERS.values():
            self.assertTrue(url.startswith("/book/#ch/"), url)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_grading -v`
Expected: `ModuleNotFoundError: No module named 'playground.grading'`.

- [ ] **Step 3: Implement**

Create `playground/grading.py`:

```python
"""The grading pass: one post-round LLM call that turns a transcript into a
failure map. The answer key (rep.KERNEL / RUBRIC / PROBES) is allowed here
and only here -- the same seam where the coach gets it in a sprint session.

Every quote is checked verbatim against the transcript in code, not trusted
from the model: an invented quote on a sales surface is the repo's standing
"never claim what the product does not do" rule broken in the visitor's own
mouth. Failures are dropped, never rendered.
"""

import json
import logging

from playground import rep

logger = logging.getLogger(__name__)

# Hand-curated: the model picks a gap_area key from this table; it does not
# mint URLs. Anchors are the free book's own hash routes (dist/book uses
# #ch/<chapter-id> -- see src/toc.json for ids).
GAP_CHAPTERS = {
    "cache_aside_vs_read_through": "/book/#ch/p1c06",
    "invalidation_race": "/book/#ch/p1c06",
    "ttl_reasoning": "/book/#ch/p1c06",
    "cold_cache_failover": "/book/#ch/p2c07",
    "stampede": "/book/#ch/p2c06",
    "capacity_numbers": "/book/#ch/p1c04",
}


def transcript_text(turns: list) -> str:
    """The candidate's words, in order, and nothing else. Turns come out of a
    live LLMContext, so content may be a string, a parts list, or missing --
    none of those may crash a grading pass."""
    out = []
    for turn in turns:
        if not isinstance(turn, dict) or turn.get("role") != "user":
            continue
        content = turn.get("content")
        if isinstance(content, str):
            out.append(content)
        elif isinstance(content, list):
            out.extend(
                part.get("text", "")
                for part in content
                if isinstance(part, dict) and part.get("text")
            )
    return "\n".join(s for s in out if s)


def build_grading_messages(turns: list, board_text: str) -> list[dict]:
    system = (
        "You are grading one short system-design interview round on: "
        f"{rep.REP_TITLE}.\n\n"
        f"The chapter says: {rep.KERNEL}\n\n"
        "A complete answer contains all of these:\n"
        + "\n".join(f"- {label}" for label in rep.RUBRIC_LABELS)
        + "\n\nThe follow-ups a strong candidate can answer:\n"
        + "\n".join(f"- Q: {p['q']}\n  A: {p['a']}" for p in rep.PROBES)
        + "\n\nFind the moments where this candidate would have been cut in a "
        "real loop. Return JSON only, exactly this shape:\n"
        '{"moments": [{"quote": "...", "probe": "...", "gap": "...", '
        '"gap_area": "..."}]}\n\n'
        "Rules:\n"
        "- At most 3 moments, and ONLY moments the transcript actually "
        "supports. Fewer is fine. An empty list is fine.\n"
        "- quote: the candidate's words, copied verbatim from the transcript. "
        "Never paraphrase, never invent.\n"
        "- probe: what was being pressed on, one line.\n"
        "- gap: the miss, named plainly, one line.\n"
        "- gap_area: exactly one of: " + ", ".join(GAP_CHAPTERS) + "."
    )
    user = "Transcript (candidate's words only):\n" + transcript_text(turns)
    if board_text:
        user += "\n\nFinal whiteboard:\n" + board_text
    return [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]


def parse_and_check(raw: str, transcript: str) -> list[dict] | None:
    """None means the model's output was unusable (caller may retry). A list
    -- possibly empty -- is a valid map: every surviving moment has a
    verbatim quote and a chapter URL resolved from GAP_CHAPTERS."""
    try:
        payload = json.loads(raw)
    except ValueError:
        return None
    if not isinstance(payload, dict) or not isinstance(payload.get("moments"), list):
        return None
    kept = []
    for moment in payload["moments"][:3]:
        if not isinstance(moment, dict):
            continue
        quote = moment.get("quote")
        probe = moment.get("probe")
        gap = moment.get("gap")
        area = moment.get("gap_area")
        if not all(isinstance(v, str) and v.strip() for v in (quote, probe, gap, area)):
            continue
        if quote not in transcript:
            continue  # invented or paraphrased: dropped, never rendered
        chapter = GAP_CHAPTERS.get(area)
        if chapter is None:
            continue  # the model does not mint URLs
        kept.append({"quote": quote, "probe": probe, "gap": gap, "chapter": chapter})
    return kept
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_grading -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add playground/grading.py playground/tests/test_grading.py
git commit -m "Grading core: answer-key prompt, verbatim-quote check, gap-to-chapter table

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: The grading call — `grade()` with one retry

**Files:**
- Modify: `playground/grading.py`
- Test: `playground/tests/test_grading.py`

**Interfaces:**
- Consumes: Task 4's functions.
- Produces: `async grade(turns: list, board_text: str, model: str, client=None) -> list[dict] | None` — `None` after two failed attempts (network error or unusable output); otherwise the checked moments list. `client` is injectable for tests; defaults to a lazily constructed `openai.AsyncOpenAI()` (reads `OPENAI_API_KEY` from the env, which `server.py`'s `load_dotenv()` has already loaded).

- [ ] **Step 1: Write the failing tests**

Append to `playground/tests/test_grading.py`:

```python
import asyncio
import json


class _FakeCompletions:
    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    async def create(self, **kwargs):
        self.calls += 1
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply

        class _Msg:
            content = reply

        class _Choice:
            message = _Msg()

        class _Resp:
            choices = [_Choice()]

        return _Resp()


class _FakeClient:
    def __init__(self, replies):
        self.completions = _FakeCompletions(replies)

        class _Chat:
            pass

        self.chat = _Chat()
        self.chat.completions = self.completions


GOOD = json.dumps(
    {
        "moments": [
            {
                "quote": "we'll just shard it",
                "probe": "the shard key",
                "gap": "no key named",
                "gap_area": "cache_aside_vs_read_through",
            }
        ]
    }
)


class TestGrade(unittest.TestCase):
    def _grade(self, replies):
        from playground.grading import grade

        client = _FakeClient(replies)
        result = asyncio.run(
            grade(TURNS, "Components: App", model="test-model", client=client)
        )
        return result, client.completions.calls

    def test_a_good_first_reply_needs_no_retry(self):
        result, calls = self._grade([GOOD])
        self.assertEqual(len(result), 1)
        self.assertEqual(calls, 1)

    def test_unusable_output_gets_exactly_one_retry(self):
        result, calls = self._grade(["not json", GOOD])
        self.assertEqual(len(result), 1)
        self.assertEqual(calls, 2)

    def test_two_failures_is_none_never_an_exception(self):
        # A buyer must never meet a broken grader: the caller turns None into
        # the honest lost-map line, so grade() must not raise.
        result, calls = self._grade([RuntimeError("api down"), RuntimeError("api down")])
        self.assertIsNone(result)
        self.assertEqual(calls, 2)

    def test_an_empty_map_is_returned_not_retried(self):
        result, calls = self._grade([json.dumps({"moments": []})])
        self.assertEqual(result, [])
        self.assertEqual(calls, 1)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_grading -v`
Expected: ImportError on `grade`.

- [ ] **Step 3: Implement**

Append to `playground/grading.py`:

```python
async def grade(turns: list, board_text: str, model: str, client=None) -> list[dict] | None:
    """One retry, then None -- the caller renders None as the honest
    lost-map line. Never raises: a buyer must never meet a broken grader at
    the moment they decide to pay, and this call sits exactly there."""
    if client is None:
        # Imported lazily so the test suite never needs the SDK's env checks.
        from openai import AsyncOpenAI

        client = AsyncOpenAI()
    messages = build_grading_messages(turns, board_text)
    transcript = transcript_text(turns)
    for attempt in (1, 2):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
            )
            moments = parse_and_check(response.choices[0].message.content or "", transcript)
            if moments is not None:
                return moments
            logger.warning("grading attempt %d returned unusable output", attempt)
        except Exception:
            logger.exception("grading attempt %d failed", attempt)
    return None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_grading -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add playground/grading.py playground/tests/test_grading.py
git commit -m "The grading call: one retry, then an honest None

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: Pipelines — build a diagnostic worker

**Files:**
- Modify: `playground/pipelines.py` (`build_playground_worker`, new `_end_diagnostic_round`)
- Test: `playground/tests/test_pipelines.py`

**Interfaces:**
- Consumes: `Session(config, kind=...)` (Task 2).
- Produces (Task 7 relies on these):
  - `build_playground_worker(connection, config, kind="sprint", on_round_end=None) -> tuple[PipelineWorker, Session]` — `kind` is forwarded to `Session`; for `kind="diagnostic"`, `end_round` is registered to `_end_diagnostic_round` and **`draw_diagram` is not registered at all**.
  - `async _end_diagnostic_round(session, on_round_end, params) -> None` — acks the tool call, then fires `asyncio.create_task(on_round_end(session))` if `on_round_end` is not None. `on_round_end: (Session) -> Awaitable[None]`.

- [ ] **Step 1: Write the failing tests**

Read `playground/tests/test_pipelines.py` first — it tests `_end_round` directly against stubs rather than building a real worker (building one loads ONNX models). Mirror that. Append:

```python
class TestEndDiagnosticRound(unittest.IsolatedAsyncioTestCase):
    async def test_it_acks_then_fires_the_round_end_callback(self):
        from playground.pipelines import _end_diagnostic_round

        session = Session(VoiceConfig(), kind="diagnostic")
        ended = []

        async def on_round_end(s):
            ended.append(s)

        acked = []

        class _Params:
            async def result_callback(self, payload):
                acked.append(payload)

        await _end_diagnostic_round(session, on_round_end, _Params())
        await asyncio.sleep(0)  # let the created task run
        self.assertEqual(acked, [{"ok": True}])
        self.assertEqual(ended, [session])

    async def test_no_callback_is_a_clean_ack_and_nothing_else(self):
        from playground.pipelines import _end_diagnostic_round

        acked = []

        class _Params:
            async def result_callback(self, payload):
                acked.append(payload)

        await _end_diagnostic_round(Session(VoiceConfig(), kind="diagnostic"), None, _Params())
        self.assertEqual(acked, [{"ok": True}])
```

(Add whatever imports the file lacks — `asyncio`, `Session`, `VoiceConfig` — following its existing import style.)

- [ ] **Step 2: Run tests to verify they fail**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_pipelines -v`
Expected: ImportError on `_end_diagnostic_round`.

- [ ] **Step 3: Implement**

In `playground/pipelines.py`, add near `_end_round`:

```python
async def _end_diagnostic_round(session: Session, on_round_end, params) -> None:
    """Handler for end_round in a diagnostic session: no coach, no voice
    switch -- the round ends in a written failure map instead. Ack first so
    the pipeline is never left waiting on a tool result, then hand off to
    the server's end path (grading, delivery, teardown) as its own task:
    grading is a full LLM call and this callback runs inside the pipeline's
    own processing."""
    await params.result_callback({"ok": True})
    if on_round_end is not None:
        asyncio.create_task(on_round_end(session))
```

(add `import asyncio` to the module's imports.)

`build_playground_worker`'s signature becomes:

```python
def build_playground_worker(
    connection: SmallWebRTCConnection,
    config: VoiceConfig,
    kind: str = "sprint",
    on_round_end=None,
) -> tuple[PipelineWorker, Session]:
```

with `session = Session(config, kind=kind)` and the registration block becoming:

```python
    if kind == "diagnostic":
        llm.register_function("end_round", partial(_end_diagnostic_round, session, on_round_end))
        # No draw_diagram: a diagnostic session never coaches, so nothing may
        # ever call it -- not registering it is the structural half of the
        # tools() guarantee.
    else:
        llm.register_function("end_round", partial(_end_round, session, tts))
        llm.register_function("draw_diagram", partial(_draw_diagram, connection))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_pipelines -v`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add playground/pipelines.py playground/tests/test_pipelines.py
git commit -m "Pipelines learn the diagnostic kind: end_round hands off to a round-end callback, no draw tool

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: Server — mode, gate, finish message, end path, diagnostic cap

**Files:**
- Modify: `playground/server.py`
- Test: `playground/tests/test_server.py`

**Interfaces:**
- Consumes: everything above.
- Produces:
  - `Mode = Literal["dictation", "playground", "diagnostic"]`
  - `_extract_finish(message: object) -> bool` — true for the client envelope `{"type": "client-message", "data": {"t": "finish", ...}}`.
  - `async _run_diagnostic_end(session, connection, config, grade_fn=grading.grade, flush_secs=1.0) -> None` — idempotent via `session.round_over`; grades, sends `{"type": "failure_map", "moments": <list|None>}` via `server_message`, waits `flush_secs`, then `_end_session(connection)` (in a `finally`).
  - `async _enforce_diagnostic_cap(connection, worker, pg_session, config, closing_secs=30.0) -> None` — no coach handover ever; requests the closing turn `closing_secs` before the cap, runs the end path at the cap if `end_round` never did.
  - The client-visible payload later tasks rely on: `{"type": "failure_map", "moments": [{"quote","probe","gap","chapter"}...] | null}` inside the standard `rtvi-ai` server-message envelope.

- [ ] **Step 1: Write the failing tests**

Read `playground/tests/test_server.py` in full first — reuse its `_FakeConnection` / `_FakeWorkerRunner` / `_FakeCapWorker` / `_FakeCapConnection` helpers and its auth-test technique (FastAPI `TestClient` with a signed token). Then append (adapting helper names to what the file actually defines):

```python
class TestExtractFinish(unittest.TestCase):
    def test_true_for_a_finish_client_message(self):
        msg = {"type": "client-message", "data": {"t": "finish", "d": {}}}
        self.assertTrue(server._extract_finish(msg))

    def test_false_for_board_messages_and_junk(self):
        self.assertFalse(server._extract_finish({"type": "client-message", "data": {"t": "board", "d": {}}}))
        self.assertFalse(server._extract_finish({"type": "other"}))
        self.assertFalse(server._extract_finish("finish"))
        self.assertFalse(server._extract_finish({"type": "client-message", "data": "finish"}))


class TestDiagnosticAuthGate(unittest.TestCase):
    # Same shape as the existing playground-gate tests: a diagnostic session
    # spends real money per minute, so it gets the same token check.
    def test_mode_diagnostic_without_a_token_is_401(self):
        response = self.client.post(
            "/api/offer?mode=diagnostic", json={"sdp": "x", "type": "offer"}
        )
        self.assertEqual(response.status_code, 401)


class TestRunDiagnosticEnd(unittest.IsolatedAsyncioTestCase):
    def _session(self):
        s = Session(VoiceConfig(), kind="diagnostic")
        s.context = _FakeContext()  # the file's existing fake, carrying get_messages()
        return s

    async def test_it_grades_sends_the_map_and_tears_down(self):
        session = self._session()
        connection = _FakeConnection()  # must record send_app_message calls
        server._sessions[connection.pc_id] = _make_fake_session_entry(connection)

        async def grade_fn(turns, board_text, model, client=None):
            return [{"quote": "q", "probe": "p", "gap": "g", "chapter": "/book/#ch/p1c06"}]

        await server._run_diagnostic_end(
            session, connection, VoiceConfig(), grade_fn=grade_fn, flush_secs=0
        )
        [sent] = connection.app_messages
        self.assertEqual(sent["label"], "rtvi-ai")
        self.assertEqual(sent["data"]["type"], "failure_map")
        self.assertEqual(len(sent["data"]["moments"]), 1)
        self.assertNotIn(connection.pc_id, server._sessions)  # torn down
        self.assertTrue(session.round_over)

    async def test_a_failed_grader_sends_null_moments_not_nothing(self):
        session = self._session()
        connection = _FakeConnection()
        server._sessions[connection.pc_id] = _make_fake_session_entry(connection)

        async def grade_fn(turns, board_text, model, client=None):
            return None

        await server._run_diagnostic_end(
            session, connection, VoiceConfig(), grade_fn=grade_fn, flush_secs=0
        )
        [sent] = connection.app_messages
        self.assertIsNone(sent["data"]["moments"])

    async def test_the_three_end_triggers_cannot_grade_twice(self):
        session = self._session()
        connection = _FakeConnection()
        server._sessions[connection.pc_id] = _make_fake_session_entry(connection)
        calls = []

        async def grade_fn(turns, board_text, model, client=None):
            calls.append(1)
            return []

        await server._run_diagnostic_end(session, connection, VoiceConfig(), grade_fn=grade_fn, flush_secs=0)
        await server._run_diagnostic_end(session, connection, VoiceConfig(), grade_fn=grade_fn, flush_secs=0)
        self.assertEqual(len(calls), 1)


class TestEnforceDiagnosticCap(unittest.IsolatedAsyncioTestCase):
    # Mirror TestEnforceCap's fakes and cadence. The two assertions that
    # matter: the closing turn is requested (announced, never a silent cut),
    # and the end path runs -- the coach handover never does.
    async def test_closing_turn_then_end_path_never_a_handover(self):
        config = VoiceConfig(diagnostic_cap_secs=0.3)
        session = Session(config, kind="diagnostic")
        session.context = _FakeContext()
        session.start(now=time.monotonic())
        connection = _FakeCapConnection()
        worker = _FakeCapWorker()  # records queued frames
        server._sessions[connection.pc_id] = _make_fake_session_entry(connection)
        ended = []

        async def grade_fn(turns, board_text, model, client=None):
            ended.append(1)
            return []

        with unittest.mock.patch.object(server.grading, "grade", grade_fn):
            await server._enforce_diagnostic_cap(
                connection, worker, session, config, closing_secs=0.1
            )
        self.assertTrue(session.closing)          # the announced closing turn
        self.assertTrue(worker.queued)            # LLMRunFrame was queued
        self.assertEqual(session.mode, "interview")  # never a coach
        self.assertEqual(ended, [1])              # the end path ran
```

Notes for the implementer, to resolve against the real file:
- `_make_fake_session_entry(connection)` stands for however the existing tests build a `server._Session` NamedTuple with a fake runner — reuse their exact pattern (`_Session(connection=..., runner=_FakeWorkerRunner(), task=..., mode="diagnostic", email="e@x", cap_task=None)`).
- If `_FakeConnection` does not yet record `send_app_message`, add `self.app_messages = []` and a `send_app_message` method to it.
- The 401 test needs the same client/env setup the existing `mode=playground` auth tests use — copy their `setUp`.
- `_FakeContext` must provide `get_messages()` returning a list; extend the existing fake with `def get_messages(self): return []` if it lacks one.

- [ ] **Step 2: Run tests to verify they fail**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_server -v`
Expected: AttributeError on `server._extract_finish` (and friends).

- [ ] **Step 3: Implement**

In `playground/server.py`:

1. `Mode = Literal["dictation", "playground", "diagnostic"]`, and add `from playground import grading` plus `from playground.relay import server_message` to the imports.

2. New parser beside `_extract_board_graph`:

```python
def _extract_finish(message: object) -> bool:
    """True for the client's finish control: {"type": "client-message",
    "data": {"t": "finish", ...}}. Same envelope walk as
    _extract_board_graph, same reason it is module-level and pure."""
    if not (isinstance(message, dict) and message.get("type") == "client-message"):
        return False
    data = message.get("data")
    return isinstance(data, dict) and data.get("t") == "finish"
```

3. The end path:

```python
async def _run_diagnostic_end(
    session: Session,
    connection: SmallWebRTCConnection,
    config: VoiceConfig,
    grade_fn=grading.grade,
    flush_secs: float = 1.0,
) -> None:
    """The one end path for all three diagnostic triggers: end_round, the
    client's finish control, and the cap. round_over makes it first-wins --
    the loop is single-threaded and there is no await between the check and
    the set, so two triggers cannot both grade. The teardown lives in a
    finally so a surprise in grading or delivery can never leave a live
    session billing with nobody coming back for it; grade_fn itself never
    raises (see grading.grade), the finally is belt for the braces."""
    if session.round_over:
        return
    session.round_over = True
    try:
        turns = session.context.get_messages() if session.context is not None else []
        board = session.board.messages()
        board_text = board[0]["content"] if board else ""
        moments = await grade_fn(turns, board_text, model=config.llm_model)
        connection.send_app_message(
            server_message({"type": "failure_map", "moments": moments})
        )
        # ponytail: fixed flush sleep before teardown; a delivery ack from the
        # client is the upgrade if maps ever go missing in practice.
        await asyncio.sleep(flush_secs)
    finally:
        await _end_session(connection)
```

4. The diagnostic cap, beside `_enforce_cap`:

```python
async def _enforce_diagnostic_cap(
    connection: SmallWebRTCConnection,
    worker: PipelineWorker,
    pg_session: Session,
    config: VoiceConfig,
    closing_secs: float = 30.0,
) -> None:
    """The diagnostic sibling of _enforce_cap. No coach handover ever --
    instead, closing_secs before the cap the interviewer is told time is up
    (Session.closing + push_context, then one LLMRunFrame: the same
    announced-not-silent mechanism the sprint handover uses), which normally
    ends the round via end_round well before the cap. If it does not, the
    cap runs the end path itself: the candidate still gets their map, just
    without a spoken goodbye. Same poll cadence and sleep maths as
    _enforce_cap, for the same recorded reasons."""
    closing_requested = False
    while connection.pc_id in _sessions:
        now = time.monotonic()
        if pg_session.expired(now):
            break
        remaining = pg_session.remaining_secs(now)
        if not closing_requested and remaining <= closing_secs and not pg_session.round_over:
            pg_session.closing = True
            pg_session.push_context()
            await worker.queue_frames([LLMRunFrame()])
            closing_requested = True
        sleep_for = remaining if closing_requested else remaining - closing_secs
        await asyncio.sleep(min(sleep_for, 1.0) if sleep_for > 0 else 0.05)
    if connection.pc_id in _sessions and not pg_session.round_over:
        await _run_diagnostic_end(pg_session, connection, config)
    else:
        # Ended by end_round/finish (their _run_diagnostic_end tears down),
        # or the visitor disconnected. Idempotent either way.
        await _end_session(connection)
```

5. In `offer()`:

- The gate condition becomes mode-set based (a diagnostic session is metered exactly like a playground one, and the recorded-mode renegotiate rule generalises):

```python
    if mode in ("playground", "diagnostic") or (
        existing is not None and existing.mode != "dictation"
    ):
        authenticated_email = _authenticate_playground_request(authorization)

    if existing is not None:
        if existing.mode != "dictation" and authenticated_email != existing.email:
            raise HTTPException(status_code=403, detail="not your session")
        ...
```

- The build branch (inside the existing `try`):

```python
        config = VoiceConfig.from_env()
        if mode in ("playground", "diagnostic"):
            if mode == "diagnostic":
                async def _on_round_end(s: Session) -> None:
                    await _run_diagnostic_end(s, connection, config)

                worker, pg_session = build_playground_worker(
                    connection, config, kind="diagnostic", on_round_end=_on_round_end
                )
            else:
                worker, pg_session = build_playground_worker(connection, config)
            pg_session.start(now=time.monotonic())

            @connection.event_handler("app-message")
            async def _on_app_message(conn: SmallWebRTCConnection, message: object) -> None:
                _apply_board_message(pg_session, message)
                if pg_session.kind == "diagnostic" and _extract_finish(message):
                    await _run_diagnostic_end(pg_session, connection, config)
        else:
            ...
```

- The cap-task creation becomes:

```python
        if pg_session is not None:
            if pg_session.kind == "diagnostic":
                cap_task = asyncio.create_task(
                    _enforce_diagnostic_cap(connection, worker, pg_session, config)
                )
            else:
                cap_task = asyncio.create_task(_enforce_cap(connection, worker, pg_session))
            _sessions[registered_pc_id] = _sessions[registered_pc_id]._replace(cap_task=cap_task)
```

- Update `offer()`'s docstring: one added sentence — `mode=diagnostic` is gated identically to `mode=playground`, and the renegotiate identity check now keys on "not dictation" rather than "playground" for the same recorded reasons.

- [ ] **Step 4: Run tests to verify they pass**

Run: `playground/.venv/bin/python -m unittest playground.tests.test_server -v`
Expected: all PASS — including every pre-existing auth/renegotiate/takeover test, unchanged. If any existing test asserts the literal string `"playground"` in gate logic, the *test* stays green because behaviour for those modes is identical; do not weaken any existing assertion.

- [ ] **Step 5: Run the full playground suite**

Run: `playground/.venv/bin/python -m unittest discover -s playground/tests -t .`
Expected: OK.

- [ ] **Step 6: Commit**

```bash
git add playground/server.py playground/tests/test_server.py
git commit -m "Wire mode=diagnostic: same gate as playground, one end path, a cap that closes instead of coaching

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: Client lib — `diagnostic` mode and failure-map parsing

**Files:**
- Modify: `sell/lib/voice.ts:34` (the `mode` union)
- Create: `sell/lib/failureMap.ts`
- Test: `sell/lib/failureMap.test.ts` (new)

**Interfaces:**
- Consumes: the server payload from Task 7: `{"type": "failure_map", "moments": [...]|null}` handed to `onMessage` as the bare `data` object (the transport unwraps the envelope — see `relay.py`'s `server_message` docstring).
- Produces (Task 9 relies on these):
  - `voice.ts`: `mode?: "dictation" | "playground" | "diagnostic"`.
  - `failureMap.ts`:
    - `export type FailureMoment = { quote: string; probe: string; gap: string; chapter: string }`
    - `export function parseFailureMap(message: unknown): { moments: FailureMoment[] | null } | null` — `null` = not a failure-map message at all; `{ moments: null }` = the grader failed (lost map); `{ moments: [...] }` = up to 3 sanitized moments, every field a non-empty string and `chapter` starting with `/book/`.

- [ ] **Step 1: Write the failing tests**

Create `sell/lib/failureMap.test.ts`:

```ts
import { test } from "node:test";
import assert from "node:assert/strict";
import { parseFailureMap } from "./failureMap.ts";

const MOMENT = {
  quote: "we'll just shard it",
  probe: "the shard key",
  gap: "no key named",
  chapter: "/book/#ch/p1c06",
};

test("a well-formed map parses", () => {
  const got = parseFailureMap({ type: "failure_map", moments: [MOMENT] });
  assert.deepEqual(got, { moments: [MOMENT] });
});

test("null moments survive as the lost-map signal", () => {
  assert.deepEqual(parseFailureMap({ type: "failure_map", moments: null }), {
    moments: null,
  });
});

test("other messages are not failure maps", () => {
  assert.equal(parseFailureMap({ type: "transcript", text: "hi" }), null);
  assert.equal(parseFailureMap("junk"), null);
  assert.equal(parseFailureMap(undefined), null);
});

test("malformed moments are dropped, not rendered", () => {
  const got = parseFailureMap({
    type: "failure_map",
    moments: [MOMENT, { quote: "" }, 42, { ...MOMENT, chapter: "https://evil.example" }],
  });
  assert.deepEqual(got, { moments: [MOMENT] });
});

test("at most three moments", () => {
  const got = parseFailureMap({ type: "failure_map", moments: [MOMENT, MOMENT, MOMENT, MOMENT] });
  assert.equal(got?.moments?.length, 3);
});

test("a moments field of the wrong shape reads as lost, not as a crash", () => {
  assert.deepEqual(parseFailureMap({ type: "failure_map", moments: "x" }), {
    moments: null,
  });
});
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd sell && npm test`
Expected: FAIL — cannot find `./failureMap.ts`.

- [ ] **Step 3: Implement**

Create `sell/lib/failureMap.ts`:

```ts
/* The failure map is the diagnostic round's whole output, and it renders on
   a page that asks for money -- so nothing from the wire is trusted. The
   server already substring-checks quotes against the transcript; this end
   checks shapes: every field a non-empty string, at most three moments, and
   chapter links only ever into the free book. */

export type FailureMoment = {
  quote: string;
  probe: string;
  gap: string;
  chapter: string;
};

const isMoment = (m: unknown): m is FailureMoment => {
  if (typeof m !== "object" || m === null) return false;
  const c = m as Record<string, unknown>;
  return (
    [c.quote, c.probe, c.gap, c.chapter].every(
      (v) => typeof v === "string" && v.trim() !== "",
    ) && (c.chapter as string).startsWith("/book/")
  );
};

/* null: not a failure-map message. { moments: null }: the round ended but
   the grader failed -- the lost-map line. { moments: [...] }: the map. */
export function parseFailureMap(
  message: unknown,
): { moments: FailureMoment[] | null } | null {
  if (typeof message !== "object" || message === null) return null;
  const m = message as { type?: unknown; moments?: unknown };
  if (m.type !== "failure_map") return null;
  if (!Array.isArray(m.moments)) return { moments: null };
  return { moments: m.moments.filter(isMoment).slice(0, 3) };
}
```

In `sell/lib/voice.ts`, the `mode` option becomes:

```ts
  mode?: "dictation" | "playground" | "diagnostic";
```

(no other change — the mode already flows into `?mode=` and the token already rides along; the server gates `diagnostic` identically to `playground`).

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd sell && npm test`
Expected: all PASS.

- [ ] **Step 5: Commit**

```bash
git add sell/lib/failureMap.ts sell/lib/failureMap.test.ts sell/lib/voice.ts
git commit -m "Client half of the failure map: parse and sanitize, plus the diagnostic mode literal

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: The page — diagnostic button, grading state, `FailureMap`

**Files:**
- Create: `sell/components/FailureMap.tsx`
- Modify: `sell/app/playground/page.tsx`
- Verify: `cd sell && npm run lint && npm run build` (build must end `○ (Static)`) and a browser check.

**Interfaces:**
- Consumes: `parseFailureMap` / `FailureMoment` (Task 8), `RESERVE_URL` / `PRICE` / `BOOK_URL` from `sell/lib/links.ts`, `connectVoice` mode `"diagnostic"`.
- Produces: `FailureMap` component, `export default function FailureMap({ moments }: { moments: FailureMoment[] | null })`.

Copy rules for every string in this task: **no em dashes**; one accent (`.btn` accent / CTA) element in the map card and none elsewhere in its viewport; the disclosure sits on the card itself.

- [ ] **Step 1: Read before writing**

Read `sell/DESIGN-SYSTEM.md` (tokens, `.btn`, accent rules) and `sell/components/Rep.tsx`'s end-of-rep CTA block (how `RESERVE_URL`/`PRICE` are used, `target="_blank"`, disclosure phrasing style). Match them.

- [ ] **Step 2: Implement `FailureMap.tsx`**

```tsx
import { BOOK_URL, PRICE, RESERVE_URL } from "@/lib/links";
import type { FailureMoment } from "@/lib/failureMap";

/* The diagnostic round's output. Three variants, all honest:
   - moments === null: the round ended but the map was lost (grader failed
     twice, or the connection died first). One line, the free book, no CTA.
   - moments === []: not enough of a round to grade. Same posture.
   - otherwise: up to three moments, the disclosure, and the one buy CTA.
   The map is the sales argument, so the standing rule bites hardest here:
   nothing renders that the transcript does not support. */
export default function FailureMap({ moments }: { moments: FailureMoment[] | null }) {
  if (moments === null) {
    return (
      <div className="failureMap">
        <p>
          The round ended before your report could be delivered. The{" "}
          <a href={BOOK_URL}>free book</a> covers everything the round probes.
        </p>
      </div>
    );
  }
  if (moments.length === 0) {
    return (
      <div className="failureMap">
        <p>
          Not enough of a round to grade. Sit a longer one, or start with the{" "}
          <a href={BOOK_URL}>free chapter</a> it draws from.
        </p>
      </div>
    );
  }
  return (
    <div className="failureMap">
      <h2>Where you would have been cut</h2>
      <ol>
        {moments.map((m, i) => (
          <li key={i}>
            <blockquote>&ldquo;{m.quote}&rdquo;</blockquote>
            <p>{m.probe}</p>
            <p>
              <strong>{m.gap}</strong>
            </p>
            <a href={m.chapter}>the free chapter that covers it</a>
          </li>
        ))}
      </ol>
      <p className="hint">
        Graded by a model against the chapter, so it can be wrong. The quotes
        are from your transcript.
      </p>
      <a className="btn" href={RESERVE_URL} target="_blank" rel="noopener">
        close these gaps in 30 days · {PRICE}
      </a>
    </div>
  );
}
```

Style `.failureMap` in `sell/app/globals.css` with the existing token set (hairline border, zero radius, reading-text sizes via `calc(Npx * var(--fs))` — copy the pattern of an existing card block). Keep the accent on the `.btn` only.

- [ ] **Step 3: Wire the page**

In `sell/app/playground/page.tsx`:

1. Extend the state union and add map state:

```tsx
type PlaygroundState =
  | "idle" | "connecting" | "live" | "grading" | "graded"
  | "ended" | "unavailable" | "denied";
```

```tsx
const [map, setMap] = useState<FailureMoment[] | null | undefined>(undefined);
const roundKind = useRef<"playground" | "diagnostic">("playground");
const gradingTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);
```

2. `start` takes the kind: `const start = useCallback(async (kind: "playground" | "diagnostic") => { roundKind.current = kind; setMap(undefined); ... connectVoice({ mode: kind, ... }) ... }, [onDraw])`. The two idle buttons call `() => start("playground")` and `() => start("diagnostic")`.

3. In `onMessage`, before the transcript branch:

```tsx
const fm = parseFailureMap(m);
if (fm) {
  if (gradingTimeout.current) clearTimeout(gradingTimeout.current);
  setMap(fm.moments);
  setState("graded");
  return;
}
```

4. A finish control for a live diagnostic round (replaces the stop button in that kind only; the sprint's stop button and its copy stay exactly as they are):

```tsx
const finish = useCallback(() => {
  session.current?.send("finish", {});
  setState("grading");
  /* The server grades, delivers, then closes. 20s is generous for one LLM
     call plus a retry; past it the honest state is a lost map, not a
     spinner that hangs on a page asking for money. */
  gradingTimeout.current = setTimeout(() => {
    setMap(null);
    setState("graded");
  }, 20_000);
}, []);
```

5. In `onDisconnect`, before the existing state set: a diagnostic round whose connection closes while the map has not arrived keeps waiting for the timeout only if we are already `grading`; otherwise (interviewer called `end_round` and the server delivered-then-closed, or the cap cut) the map either already arrived (state is `graded` — keep it) or is lost:

```tsx
onDisconnect: (reason) => {
  if (session.current !== opened) return;
  session.current = null;
  if (roundKind.current === "diagnostic" && reason !== "error") {
    setState((s) => {
      if (s === "graded") return s;          // map already rendered
      if (s === "grading") return s;         // timeout decides
      setMap(null);                          // closed before any map
      return "graded";
    });
    return;
  }
  setState(reason === "error" ? "unavailable" : "ended");
},
```

(The `setMap` call inside the updater is impure — hoist it: compute next state first, call `setMap(null)` outside when needed. Implement it as two plain reads of a `stateRef` if the file already tracks one; otherwise track the latest state in a ref alongside `setState`, the standard pattern. Keep it simple and lint-clean.)

6. Render: while `state === "grading"`, a single line (`<p className="hint">Grading your round now. Your report lands here in a few seconds.</p>`); while `state === "graded"`, `<FailureMap moments={map ?? null} />` plus a plain (non-accent) "sit another round" button that calls `start("diagnostic")`. Add the diagnostic start button beside the existing one when signed in and not live:

```tsx
<button type="button" className="btn" onClick={() => start("diagnostic")} disabled={state === "connecting"}>
  sit the diagnostic round (6 min)
</button>
<p className="hint">
  A short interview, no coach. It ends in a written report: the moments
  where you would have been cut, in your own words, each linked to the free
  chapter that covers it.
</p>
```

Mind the accent rule: if both start buttons render accent `.btn`, demote one (check `DESIGN-SYSTEM.md` for the non-accent button class and use it on the sprint-playground button — the diagnostic round is this page's primary action now). Also the unmount teardown effect stays exactly as is — a diagnostic visitor who navigates away mid-round is torn down like any other.

7. Update the live-state hint and controls: when `state === "live" && roundKind.current === "diagnostic"`, the button reads `finish and get my report` and calls `finish`; hint: `Ends the interview and grades it. The report appears here.`

- [ ] **Step 4: Lint, test, build**

Run: `cd sell && npm run lint && npm test && npm run build`
Expected: lint clean; tests pass; build ends `○ (Static)`.
Also run: `grep -c '—' sell/out/playground/index.html` — expected `0` (and the page's new strings contain none by construction).

- [ ] **Step 5: Browser verification (no OpenAI key needed for these)**

Start the service and the page:

```bash
playground/.venv/bin/uvicorn playground.server:app --port 7860 --app-dir . &
cd sell && npm run dev
```

In a real browser (Playwright MCP is available) at `http://localhost:3000/playground`:
- Signed out: Google button renders, both start buttons absent.
- The `graded` states render correctly: in devtools, temporarily drive the component by evaluating the page with a fixture — or simpler, add nothing and instead verify `FailureMap` variants by rendering it on the page during dev only if trivially possible; otherwise verify the three variants by unit of eye: run `npm run dev`, edit `page.tsx` momentarily to `const [map] = useState<FailureMoment[] | null | undefined>([{quote: "we'll just shard it", probe: "the shard key", gap: "no key named", chapter: "/book/#ch/p1c06"}]); const [state] = useState<PlaygroundState>("graded")`, look at it (accent count, disclosure, link), then revert the edit before committing. Screenshot the map card.
- A full live round end-to-end needs a real `OPENAI_API_KEY` and a signed-in Google account; that run is the user's acceptance step, not this task's gate. Say so in the task's completion report.

- [ ] **Step 6: Commit**

```bash
git add sell/components/FailureMap.tsx sell/app/playground/page.tsx sell/app/globals.css
git commit -m "The diagnostic round on the page: finish control, grading state, the failure map with its one CTA

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 10: Docs, PROGRESS entry, full verification

**Files:**
- Modify: `playground/README.md` (Auth section), `sell/PROGRESS.md` (append entry)

**Interfaces:** none — documentation and the final gate.

- [ ] **Step 1: README**

In `playground/README.md`'s Auth section, the first sentence becomes: "`mode=playground` and `mode=diagnostic` on `POST /api/offer` require a Google sign-in; `mode=dictation` needs nothing and stays completely open …" (rest unchanged).

- [ ] **Step 2: PROGRESS entry**

Append to `sell/PROGRESS.md` (newest at the bottom, what/why/how, per its conventions — note the file already carries uncommitted text from other work; append below it and stage the whole file only in this commit, which is the one place that in-flight entry gets carried in deliberately — flag that in the commit message):

```markdown
## 2026-08-23 — the diagnostic round: a free interview that ends in a failure map

**What:** a third voice-service mode, `diagnostic`. A signed-in visitor sits a
~6-minute interviewer-only round on the cache-aside rep; the round ends in a
written failure map — up to three moments quoted verbatim from their own
transcript, the gap each exposes, the free chapter that covers it, and the one
buy CTA. No coach: the walkthrough is what the sprint sells. Spec:
`../docs/superpowers/specs/2026-08-23-diagnostic-round-design.md`.

**Why this shape:** the market sells content and asks the buyer to imagine
their gap; this shows the gap, in the visitor's own words. The map replaces
the walkthrough honestly — the book is the free answer key, so what is
withheld is the service, not the information.

**How:** `Session` gained a `kind`; a diagnostic session runs under its own
cap (`PLAYGROUND_DIAGNOSTIC_CAP_SECS`, default 360), can never switch to
coach (structural: `switch_to_coach` raises, `draw_diagram` is never
registered), and its interviewer prompt is starved of the answer key exactly
like the sprint one. The key enters once, post-round, in
`playground/grading.py`: one LLM call, one retry, output schema-checked and
every quote substring-checked against the transcript in code — invented
quotes are dropped, never rendered, and the model picks chapters from a
hand-curated table rather than minting URLs. All three end triggers
(`end_round`, the client's finish control, the cap) converge on one
idempotent end path that grades, delivers `{"type": "failure_map"}` over the
existing app-message channel, and tears down; the cap requests an announced
closing turn 30s out instead of a coach handover. Client: `parseFailureMap`
sanitizes shapes and pins chapter links to `/book/`; the page gained
`grading`/`graded` states, a 20s lost-map timeout, and the `FailureMap` card
whose empty and lost variants carry no CTA. Local only — hosting, spend
guards, the §1/§9 copy re-read and the rsync exclude reversal are one
deliberate package recorded in the spec as "the hosting gate".
```

- [ ] **Step 3: Full verification**

```bash
playground/.venv/bin/python -m unittest discover -s playground/tests -t .
cd sell && npm run lint && npm test && npm run build
```

Expected: all green, build `○ (Static)`. Report exact counts.

- [ ] **Step 4: Commit**

```bash
git add playground/README.md sell/PROGRESS.md
git commit -m "Document the diagnostic round: README auth note and the PROGRESS entry

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

## Self-Review (performed at plan-writing time)

- **Spec coverage:** cap knob (T1), kind/no-coach/no-draw (T2, T6), persona starvation (T3), grading with verbatim check + table + retry + None (T4, T5), one end path with idempotency + delivery + teardown (T7), announced cap closing (T7), auth gate parity (T7), client parse/sanitize + mode literal (T8), page states + finish control + FailureMap variants + one-CTA + disclosure + no-em-dash (T9), docs + PROGRESS (T10). Hosting gate: deliberately untouched, constraint recorded globally.
- **Placeholders:** none — every step carries code or an exact command. The two "adapt to the file's existing fakes" notes in T7 name exactly which helpers and what to add to them.
- **Type consistency:** `kind: "sprint"|"diagnostic"` (T2→T6→T7→T9's `roundKind` uses `"playground"|"diagnostic"` — different axis: it is the client's connect mode, matching `voice.ts`'s union from T8, not `Session.kind`); `grade(turns, board_text, model, client)` (T5) matches T7's `grade_fn` call signature; the wire payload `{"type": "failure_map", "moments": list|null}` (T7) matches `parseFailureMap` (T8) and `FailureMap`'s prop (T9); `FailureMoment` fields match `parse_and_check`'s output keys.
