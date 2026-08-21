# Playground and Dictation — Design Spec

Date: 2026-08-21 · Status: approved by user (chat) · Companion to `2026-08-13-hld-gym-design.md`

Closes the open item `sell/PROGRESS.md` has carried since 2026-08-16: *"Playground
unspecified. A live coach that talks while you draw, keeps you thinking aloud, and
unsticks you. No spec, no chosen stack, no cost model for realtime audio."*

## What this is

Two features that share one voice pipeline and one connection.

| | what it does | size |
|---|---|---|
| **Dictation** | you speak your rep answer instead of typing it, hands-free | small |
| **Playground** | a live session: you draw on a whiteboard and think aloud, an interviewer pushes back, then a coach walks you through what you missed | the largest build in this product |

Dictation is Playground's pipeline with two stages removed. That is the reason they are
one spec and one service rather than two.

### Scope of the first build

**One rep.** The only rep that exists is `p1c06 · cache-aside read path`
(`sell/lib/rep.ts`), and the first Playground session is that one, with its kernel,
`RUBRIC` and `PROBES` hand-fed into the coach prompt. Generalising to a rep-per-chapter
content pipeline is a separate piece of work and is not designed here — doing it before
one session has been sat through would be designing against a guess.

**Dictation lands in the existing recall textarea** in `sell/components/Rep.tsx`, next
to the keyboard, never replacing it. Its pipeline is `transport.input() -> stt ->
app message`; no LLM, no TTS. The client appends each finalised transcript to the
textarea's existing `recall` state, so the regex rubric grades spoken and typed answers
through exactly the same path.

## What exists today, precisely

`sell/components/Rep.tsx` animates one hand-laid SVG (`Diagram.tsx`), locks it, and asks
the visitor to **type** what they remember into a textarea. `RUBRIC` in `sell/lib/rep.ts`
is six regexes over that text. Three probe textareas below it are not wired to anything.

There is no microphone path and **no drawing surface anywhere in this repository.** The
whiteboard is a new build, not an extension of `Diagram.tsx` — that file is one specific
diagram with CSS draw animations, not a canvas.

## Decisions, and the reasoning worth keeping

**Pipecat, cascaded — not speech-to-speech.** The pipeline is
`mic → VAD → STT → LLM → TTS → speaker` with three separate OpenAI services, not one
realtime speech-to-speech model. Speech-to-speech is lower latency and better prosody,
and it is the obvious upgrade. It is not first because it takes the turn-detection
decision away from us and hands it to a provider's `server_vad` config — and turn
detection is the thing that decides whether this feels like an interview or like being
talked over. Cascaded also produces real text at every stage, which the existing
`RUBRIC` grades for free. Pipecat makes the swap a service substitution later, which is
the reason to accept a framework at all.

**`SmallWebRTCTransport`, not Daily.** No vendor account, no per-minute transport bill,
runs on a laptop. Daily is the answer if this ever needs to scale past one user at a
time; it is not the answer for finding out whether the thing is any good.

**Silero VAD plus SmartTurn.** Both run locally on the server as ONNX models. Neither
costs anything per minute. Only STT, LLM and TTS bill.

**The interviewer never holds the answer key.** See §"Session state". This is a
correctness property, not a style choice.

**The model emits topology, never coordinates.** See §"The coach drawing back".

**"Teach people" resolved as: the product teaches.** The coach half teaches system
design from the chapter the rep came from. A book chapter *about* realtime voice
architecture — VAD, endpointing, barge-in, the latency budget — is a genuinely good fit
beside the WebSocket and streaming chapters and is **explicitly out of scope here**. It
is parked, not rejected.

## Turn detection — the part that decides whether this feels good

Two listeners must agree before the user's turn ends:

1. **`SileroVADAnalyzer(params=VADParams(stop_secs=...))`** — raw silence. Tuned short,
   it cuts people off mid-thought. Tuned long, every sentence is followed by dead air.
2. **SmartTurn** — semantic endpointing. *"So the app checks the cache first, and…"* is
   silence but is not a finished turn. Silence alone produces an interviewer that talks
   over you, which is the single failure most likely to kill the feature.

`min_volume` is the third knob, for rooms with background noise retriggering the VAD.

These are tuned by ear against real sessions, not left at library defaults. The spec
records them as knobs on purpose: no default survives contact with a real microphone in
a real room.

**Dictation runs the same VAD with a longer `stop_secs`,** because someone drawing a
diagram pauses far longer than someone in conversation. Hands-free is the entire
justification for VAD here — you cannot click a stop button while you are drawing, so
the VAD *is* the stop button.

Exact class names and import paths are pinned against the installed `pipecat-ai`
version at implementation time. That API has moved between releases; remembered imports
do not ship.

## The whiteboard

**Excalidraw (`@excalidraw/excalidraw`, MIT).**

Two reasons, one load-bearing. First, it is what remote onsites actually hand a
candidate, and AGENTS.md's standing rule is that every format decision is justified by
**output mode matching the interview** — never by preference. Second, its elements are
already structured: a rectangle carries `boundElements` (its label), an arrow carries
`startBinding.elementId` and `endBinding.elementId`. Extraction is a walk over that,
not computer vision.

Rejected, with reasons:

- **React Flow** — nodes and edges free, no extractor needed, but components are dragged
  off a palette, so you cannot forget a component's name. It makes the exercise easier
  than the thing it simulates.
- **Roll our own SVG** — this repo hand-lays SVG well, but drag, binding, undo and text
  editing is a month of work to arrive at a worse Excalidraw.
- **tldraw** — good editor API; licensing carries a watermark tier.

## Reading the board

Not screenshots. The canvas serializes to a labelled graph:

```
{nodes: [{id, label}], edges: [{from, to, label}], unreadable: n}
```

Roughly 200 tokens, exact, and — the reason it wins — **diffable**. "They drew Cache→DB
before App→Cache" and "they have not touched the board in forty seconds" are the signals
a coach that unsticks people runs on. A vision snapshot has no memory of the previous
frame and cannot produce either.

Transport: RTVI app messages over the **same** peer connection as the audio. No second
websocket.

Cadence: debounced ~800ms after the last change, sent only when the serialized graph
differs from the last one sent. This is VAD for the board, and it has the same shape as
the audio one.

Context discipline: the board lives in the LLM context as **one message, replaced in
place, never appended**, plus one short recent-event line (`just added: Cache→DB`). A
ten-minute session must not accumulate two hundred copies of a diagram.

Two extractor rules, both bugs waiting to happen if left implicit:

- **Coach-drawn elements are tagged and excluded from extraction.** Otherwise the coach
  reads its own diagram back and congratulates the user on it.
- **Freehand strokes count as `unreadable: n`** and the coach is instructed to ask the
  user to name them aloud rather than guess. The user is talking anyway; transcript plus
  graph beats either alone.

## The coach drawing back

The LLM tool is `draw_diagram(nodes, edges)` — **no coordinates**. The client receives
topology, runs `@dagrejs/dagre` (Sugiyama layered, ~100KB) for x/y, feeds
`convertToExcalidrawElements`, and calls `excalidrawAPI.updateScene`.

It renders into **its own lane**, offset beside the user's work. It never mutates user
elements. Two reasons, and both are the reason the tool signature has no x/y: a model
placing shapes by hand produces a tangle, and a coach drawing into the user's diagram
would later read its own work back as theirs.

`elkjs` is the named upgrade if dagre's layouts look tangled — same input contract, so a
swap rather than a rewrite.

This is the highest-risk item in the build. It is in scope because the user chose it
over annotation-only after being shown that trade.

## Session state

Two modes, one variable, two system prompts. Not `pipecat-flows` — two states are not a
state machine.

| | interviewer | coach |
|---|---|---|
| in context | the board, the running transcript, the question | all of that **plus** the chapter kernel, `RUBRIC` labels, `PROBES` answers |
| tools | `end_round(reason)` | `draw_diagram(nodes, edges)` |
| TTS voice | one voice | **a different one** |

**The interviewer must not have the answer key in context.** A model holding the answers
leaks them the moment a candidate sounds stuck, and then the round graded nothing. The
key enters the session only at the handoff.

The handoff is triggered by `end_round`, by an explicit "I'm done" control, or by the
session cap. **It must be audible** — different voice, and a line that names the switch —
or it reads as the interviewer having gone soft rather than as a change of role.

`SYSTEM.md` §1 already names this tension: *"an interviewer that pushes back" and "a
coach that helps" are opposite promises to a buyer.* Switching between them in one
session is the resolution, and it only works if the seam is loud.

## Where the code lives

```
playground/            FastAPI + Pipecat bot. Holds the OpenAI key.      (new)
sell/app/playground/   the client route: Excalidraw + dagre + pipecat client-js
```

The client sits inside `sell/` rather than in a second frontend toolchain so it inherits
`globals.css`, DESIGN-SYSTEM.md and the theme cycle, and looks like the product instead
of a demo. Next code-splits per route, so `/` never pays for the Excalidraw bundle.

The server is separate because it is Python and holds a key.

**AGENTS.md opens "one repo, three pipelines".** This makes four, and that line is
updated as part of the work rather than left standing and contradicted.

## Failure modes

- **Mic permission denied** → text mode, and the page says so out loud.
- **Service down, WebRTC fails, OpenAI 429 or timeout** → the existing rep works exactly
  as it does today: type the answer, get the regex score. This is the same
  non-negotiable already on record for LLM grading — *a buyer must never meet a broken
  grader at the moment they decide to pay.*
- **Cost runaway** → a hard wall-clock cap per session, announced at the start, not
  enforced silently at the moment it bites.
- **Noisy room retriggering VAD** → `min_volume`, tuned by ear.

## Cost

Cascaded runs materially cheaper per minute than a realtime speech-to-speech model. The
multiple is not recorded here because current OpenAI per-minute pricing is checked live
before any per-minute model is committed to — a remembered price on a page or in a
budget is how a product ends up selling something it cannot afford to run.

## Testing

One runnable check per piece that can rot silently. No frameworks, no fixtures beyond
what the assertion needs.

- **`extract.test.ts`** — a fixture scene containing a bound arrow, a container label, a
  freehand stroke, and one coach-tagged element. Asserts the extracted graph, and
  asserts the coach element is absent. Highest-value test in the build.
- **Mode switch** — asserts the interviewer context contains no answer key and the coach
  context does.
- No faked WebRTC peers. The transport is IO; it is tested by using it.

## Deliberately unresolved

- **Hosting.** Whether any of this deploys, and where, is not decided here. The user
  set it aside explicitly to keep the design about value rather than infrastructure.
  It collides with AGENTS.md's *"No backend, no auth, no database until someone pays"*
  and that conversation happens on its own, with a running thing to look at.
- **The voice-pipeline chapter.** Parked, see above.
- **Whether Playground ever appears on the sell page.** `SYSTEM.md` §1 warns that if it
  ships, the *What you are not buying* copy and §9 must be re-read line by line. Nothing
  goes on the page until that re-read happens.
