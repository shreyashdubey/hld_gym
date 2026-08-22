# The Diagnostic Round — Design Spec

Date: 2026-08-23 · Status: approved by user (chat) · Companion to
`2026-08-21-playground-design.md`

## What this is

The market sells content and asks the buyer to imagine their gap. This sells
the diagnosis: a stranger sits a real voice interview and is shown, in their
own words, exactly where they would have been cut.

A third mode on the voice service, `diagnostic`: the existing Playground
pipeline and the existing rep (`p1c06 · cache-aside read path`), interviewer
only, capped at ~6 minutes. The round does not end in a coach walkthrough. It
ends in a **failure map**: up to three moments from the transcript, each one a
verbatim quote of the candidate, the probe that exposed it, the gap named in
one line, and a link to the free chapter that covers it — with the one buy CTA
underneath. The map is the sales argument; the walkthrough is what $19 buys.

The Sprint playground (interviewer → coach) is unchanged.

## Decisions, and the reasoning worth keeping

**Map only — the coach does not appear in the free round.** Chosen by the user
over coach-then-map. Three reasons: it halves the OpenAI minutes a stranger
can spend; it keeps the paid product's core off the free tier; and it makes
the sell honest rather than hollow — the visitor still leaves with the map and
the free chapters, which are the answer key, so "no walkthrough" is a
withheld *service*, not withheld *information*. The book stays the answer
key; the product stays the practice.

**Local only, for now.** The user chose to spec and build this behind
localhost and defer hosting. Everything below runs against the dev setup in
`playground/README.md`. Going public is a single recorded package — see "The
hosting gate" — and nothing lands on the sell page until that gate is passed
deliberately.

**Same Google gate as `mode=playground`.** A diagnostic session spends real
money per minute; it gets the same `Authorization: Bearer` check on
`/api/offer`, the same renegotiate identity check, the same everything.
`mode=dictation` remains the only open mode.

**Grading happens after the round, or the round graded nothing.** The
interviewer-never-holds-the-answer-key invariant from the playground spec
carries over unchanged: during the round the diagnostic interviewer's context
contains no KERNEL, no RUBRIC, no PROBES. The key enters exactly once, in the
grading pass, after the last user turn — the same seam where the coach gets
it today.

**Quotes are verbatim or they are dropped.** Each moment's `quote` must be a
substring of the actual transcript, checked in code, not trusted from the
model. A moment whose quote fails the check is discarded and the map renders
with fewer moments. An invented quote on a sales surface is the standing
"never claim what the product does not do" rule broken in the worst possible
place — in the visitor's own mouth.

**Up to three moments, not exactly three.** A visitor who says four sentences
and clicks finish has not produced three failures worth quoting. The grader
is told: only moments the transcript actually supports. Zero moments renders
an honest card — "not enough of a round to grade" — with the book link and no
CTA theatrics.

**Delivery over the existing channel, held in memory, gone when it's gone.**
The map travels as a server app message (`{type: "failure_map", ...}`) over
the still-open connection — the same `send_app_message` path `draw` uses —
and then the session tears down. No database, no report endpoint, no
persistence; consistent with the no-backend posture. If the connection dies
before delivery, the map is lost and the client says one honest line and
links the chapter. Acceptable for a free tier.

**One end path.** Three triggers — the interviewer's `end_round`, the
visitor's finish button, the cap — all converge on the same sequence:
interviewer's closing line (cap case only), grading pass, delivery, teardown.
In diagnostic mode the client's stop control becomes "finish — get my
report" and sends a client app message instead of hanging up, because a hard
disconnect is the one trigger that cannot deliver a map.

## The round

- **Cap:** `PLAYGROUND_DIAGNOSTIC_CAP_SECS`, default `360` (6 minutes), a
  `VoiceConfig` field like the others. Announced up front on the page, same
  rule as the playground cap: never enforced silently.
- **No handover branch.** The cap-enforcement path for a diagnostic session
  has no 80% coach switch. At the cap it queues one final interviewer turn
  ("that's time...") — announced, not a mid-sentence cut — then runs the end
  path.
- **Tools:** the diagnostic interviewer gets `end_round` only, and there is
  no mode in which a diagnostic session ever gets `draw_diagram` — asserted
  in tests, same class of invariant as the answer-key starvation.
- **Persona:** the existing interviewer prompt with a diagnostic close: run a
  tight round on the rep, probe where they hand-wave, call `end_round` when
  the round has shown what it is going to show. It still never hints and
  never teaches.

## The grading pass

One non-voice LLM call (`PLAYGROUND_LLM_MODEL`, same client the pipeline
already holds), in a new `playground/grading.py`, so it is unit-testable
without a live pipeline.

**Input:** the conversation turns from the bound LLM context (user and
assistant, not the system messages), the final board graph from
`BoardContext`, and — only here — `rep.KERNEL`, `rep.RUBRIC_LABELS`,
`rep.PROBES`.

**Output**, schema-validated before anything is sent:

```
{"moments": [{"quote": str, "probe": str, "gap": str, "chapter": str}, ...]}  # 0–3
```

- `quote` — candidate's words, verbatim, substring-checked against the
  transcript in code; failures dropped.
- `probe` — what the interviewer was pressing on, one line.
- `gap` — the miss, named plainly, one line. Written to sting and to be
  accurate, in that order of difficulty and the reverse order of priority.
- `chapter` — chosen from a hand-curated table in `grading.py` mapping this
  rep's known gap areas (invalidation race, cold-cache failover, TTL
  reasoning, cache-aside vs read-through, stampede) to anchors in the free
  `/book/`. The model picks from the table; it does not mint URLs.

**Failure handling:** the grading call gets one retry; after that the client
receives `{type: "failure_map", "moments": null}` and renders the lost-map
line. A buyer must never meet a broken grader at the moment they decide to
pay — the degraded state is honest and quiet, never a spinner that hangs or a
fake map.

## The client

`sell/app/playground/page.tsx` grows a second start button — "sit the
diagnostic round (6 min)" — beside the existing one, both behind the same
sign-in. New states: `grading` (finish sent, map not yet arrived, ~20s
timeout into the lost-map line) and `graded`.

`sell/components/FailureMap.tsx` renders the map: up to three moments — the
quote, the probe, the gap, the free-chapter link — then the **one** accent
CTA (`RESERVE_URL`, `PRICE` from `lib/links.ts`). One accent action in the
viewport; the moments' chapter links are text links.

Disclosure, on the card, where the belief forms, same pattern as the
keyword-score note in `Rep.tsx`: *graded by a model against the chapter, so
it can be wrong; the quotes are from your transcript.*

Board, mic-denied handling, sign-in flow, dictation: all unchanged.

## The hosting gate — deliberately deferred, as one package

None of the following is built now, and all of it happens together, on
purpose, when the user decides the round goes public:

1. Hosting with real UDP ingress (small VPS or Fly.io — Railway and Render
   cannot carry WebRTC).
2. `PLAYGROUND_ALLOWED_ORIGINS` widened to the real origin, deliberately.
3. Spend guards that only matter in public: a daily round counter and a
   concurrent-session cap, both in-memory.
4. The `SYSTEM.md` §1 / §9 line-by-line re-read of *What you are not buying*
   that the playground spec already requires before anything voice-shaped
   touches the sell page.
5. Reversing `publish:book`'s `--exclude 'playground/'` — by decision, not
   accident (`../AGENTS.md`).
6. The sell-page CTA to the round.

Until then the diagnostic round exists at `localhost:3000/playground` against
a `localhost:7860` service, demoable end to end.

## Failure modes

- **Mic denied / service down / WebRTC fails** — exactly today's handling;
  nothing new.
- **Connection dies before delivery** — map lost; one honest line plus the
  book link.
- **Thin transcript** — fewer moments, or the not-enough-to-grade card.
- **Grader fails twice** — lost-map line, see above.
- **Cap hits mid-sentence** — the closing turn is queued at the cap, then the
  end path runs; the cut is announced, never silent.

## Cost

Interviewer-only at a 6-minute cap is materially less than half of today's
12-minute two-persona session; the grading pass adds one text-only LLM call.
No new metered service. Per-minute prices are checked live before any public
launch, per the playground spec's rule — a remembered price is how a product
sells something it cannot afford to run.

## Testing

One runnable check per piece that can rot silently:

- The diagnostic interviewer's context contains no KERNEL / RUBRIC / PROBES
  string; the grading input does. Mirror of the existing mode-switch test.
- A diagnostic session's tool list never contains `draw_diagram`, in any
  state.
- The quote substring check: a fabricated quote is dropped, a verbatim one
  survives, zero surviving moments still produces a valid payload.
- The cap path in diagnostic mode runs the end path and never the coach
  handover.
- `FailureMap` renders a fixture map: three moments, one accent CTA, the
  disclosure line present.

## Files

```
playground/config.py       diagnostic_cap_secs
playground/session.py      session kind: sprint | diagnostic
playground/personas.py     diagnostic interviewer close; grader prompt
playground/grading.py      new — grading call, schema check, quote check, gap→chapter table
playground/server.py       mode=diagnostic, cap variant, finish message, delivery
sell/app/playground/page.tsx   second button, grading/graded states
sell/components/FailureMap.tsx new
tests on both sides, per above
```
