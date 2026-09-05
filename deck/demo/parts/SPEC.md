# Persona slides spec — three people, two slides each

Deck: one file, `deck/demo/index.html`, hosted at `/demo/`. Shell (slides 1–3 and 10) is built by another agent. Each persona agent writes ONE fragment file, `deck/demo/parts/persona-<a|b|c>.html`, containing exactly:

```html
<section class="slide" data-persona="a"> … profile → generated … </section>
<section class="slide" data-auto="a"> … the experience stage … </section>
<style> /* every rule scoped under .pa- (or .pb- / .pc-) classes; no bare element selectors, no ids */ </style>
<script> deckAuto.register('a', { start(section) { … }, stop() { … } }); </script>
```

The assembler inlines the fragment in place of `<!-- PERSONA:A -->` etc. No `<html>`, `<head>`, `<body>`, no external requests, no images (draw everything in CSS/SVG). Names are constants at the top of the `<script>` (`const NAME = "…"`) AND written literally in the markup; the presenter may replace them.

## Contract with the shell

- Tokens exist on `:root` / `[data-theme="dark"]`: `--paper --panel --panel-2 --ink --ink-2 --ink-3 --line --line-strong --accent --accent-ink --accent-soft --good --good-soft --bad --bad-soft --on-accent --font-ui (Archivo) --font-mono (IBM Plex Mono) --font-read (Literata)`.
- The shell gives every `.slide` `display:flex; flex-direction:column; position:absolute; inset:0; padding:6vmin 8vmin` and the `.kicker`, `h1`, `.lead`, `.foot` styles of `deck/index.html` (copy those classes' look; you may use them). Everything else you style yourself under your prefix.
- `window.deckAuto.register(id, {start, stop})` exists before your script runs. `start(section)` is called ~250 ms after your experience slide becomes visible, `stop()` when it is left; `r` calls stop then start. `start` must be idempotent: clear all timers/classes in `stop()` and at the top of `start()`. Use `setTimeout` chains or a single `requestAnimationFrame` timeline; never `setInterval` without clearing.
- When the timeline ends, HOLD the final frame and show a small mono hint bottom-right of the stage: `r · replay`. Do not loop.
- Zero border-radius. 1px hairlines. No shadows, gradients, emoji, images. One accent element per slide (the kicker is not one; a highlighted diagram node / the drawing arrow / a score number counts as the one). Mono lowercase for chrome, Archivo for headings, Literata for prose and anything the person "types". No scrolling at 1280×720 or 1920×1080: assert it.
- Legibility: nothing under 1.8vmin. The stage's "one big cue" per phase must survive a back row: the question, the lock box, the score, the final "where it breaks" line.
- Nothing is sold. No price, no CTA, no "reserve".

## Slide layout, same for all three

**Profile slide** (`data-persona`): kicker `PERSON A · SHREYASH · BACKEND ENGINEER → SENIOR SYSTEM-DESIGN BAR` (pattern: person · name · from → to). `h1` one line about them (given below). Then a two-column hairline `.split`:
- LEFT, h2 `extracted · by hand, in conversation`: a definition list, 8 rows, mono key (lowercase, `--ink-3`, ~1.9vmin) + Literata value (~2.1vmin): `intake`, `retention`, `recall`, `retrieval mode`, `thinking`, `attention`, `prior knowledge`, `calibration`. Values given below, verbatim.
- RIGHT, h2 `generated · the book for that head`: book title in Archivo 700 (~2.8vmin), one line on structure, then a 7-row list, mono tag (`chapters`, `interactive diagrams`, `simulations`, `micro-games`, `challenges`, `reels`, `lock & ask`) + one concrete example each (given below). The tag column in `--ink-3`; the example in Literata.
- `.foot` left: the named techniques for this person; right: `next: what <name> experiences`.

**Experience slide** (`data-auto`): kicker `<NAME> · <CHAPTER TITLE> · <one-line problem>`; the stage fills the rest (a `.rep`-like panel: 1px `--line-strong` border, `--panel` ground, an orange `.repTag`-style strip on top with the chapter id left and the current phase right, lowercase mono). Inside, the phases below play automatically with the given timings. Phase names in the strip: `watch · lock · rebuild · grade · probe · reveal` (B and C have their own phase names below). Timeline total 50–60 s.

---

# PERSON A · Shreyash (real name, the founder)

Kicker: `PERSON A · SHREYASH · BACKEND ENGINEER → SENIOR SYSTEM-DESIGN BAR`
h1: `Wants to know who got hurt before he wants the mechanism. Forgets both unless he has to redraw them.`

extracted:
- intake — Origins first: who hit the problem, what they were stuck on, how they got to the answer. A mechanism with no story is a fact; with a story it is a decision he can re-make. Then diagrams before prose: the whole shape first, then the edges.
- retention — Sticks when he has to redraw it from nothing. Dies when he reads it twice and feels fluent.
- recall — Out loud, at a whiteboard, while someone asks why. Silent recall is not the shape of the exam.
- retrieval mode — Closed-book rebuild of the diagram, then an interviewer probing the edge he left out.
- thinking — Top-down. "What is the invariant?" first, mechanism second, code last.
- attention — Long prose kills it. One screen, one idea, one drawing.
- prior knowledge — Strong on APIs and databases. Weak on where things break at scale and at 3 a.m.
- calibration — Overconfident after reading. Called five of six on stage, scored four.

generated: **HLD Gym** — 51 chapters, ordered problem-before-solution; each chapter one kernel, one drawing, one place it breaks; every chapter also exists story-first, as its origin.
- origins — The same 51 chapters told from the person who hit the wall: Dalmellington, 2015, one £8,000 pouch scanned once and recorded four times; the retry was honest. Who got hurt, what nobody had remembered, then the mechanism. (The `origins` row goes first in the list, making it 8 rows.)
- chapters — Part 1 is the read path, Part 2 is what breaks when two things happen at once, Part 3 is systems that survive it. Each chapter opens with the pain, then the mechanism.
- interactive diagrams — 197 diagrams that draw themselves step by step with narration; edges animate in order so cause precedes effect.
- simulations — Failure injection in the probes: the cache dies at 10×, the lease expires mid-write, the retry lands during the transaction.
- micro-games — Cards: people, incidents, papers, years. Seema Misra, 2010: "the computer did it" as a defence in front of a jury; the Dalmellington bug; Bates v Post Office, 2019. Say who, when, and what they had to remember, before the card flips.
- challenges — A checkpoint at the end of every chapter; the kernel names where it breaks and the checkpoint asks there.
- reels — Four so far: "a lock is a statement about the past", "R + W > N", "queueing is refusing slowly", "the cache is a suggestion".
- lock & ask — The diagram disappears. He rebuilds it. An interviewer takes the answer apart. Then the chapter shows what it says.

foot left: `retrieval practice · transfer-appropriate practice (whiteboard + speaking) · dual coding · desirable difficulty · calibration (judgment of learning before reveal)`; foot right: `next: what Shreyash experiences`.

## A · experience — chapter `p2c02 · Idempotency, Exactly-Once, and Ledgers`

Kicker: `SHREYASH · P2C02 · IDEMPOTENCY, EXACTLY-ONCE, AND LEDGERS · you tapped pay, the signal died, you were not charged twice`

Strip phases: `question · origin · watch · lock · rebuild · grade · probe · reveal`. All later timings below shift by +8 s after the origin phase (total ~64 s).

Timeline (seconds from start):
- 0–4 **question**: strip phase `question`. Centred Archivo 800 at ~5vmin: `You tapped Pay. Your signal died. The app retried.` line 2 in `--ink-2`: `Why weren't you charged twice?`
- 4–12 **origin**: one hairline card, `--panel-2` ground, mono eyebrow `origin · dalmellington, 2015 · horizon online, fujitsu / post office`, Archivo 700 ~3.2vmin: `The books balanced. The books were wrong.`, Literata ~2.2vmin: `A subpostmistress scanned one £8,000 pouch once. Horizon recorded it four times. The retry was honest: a script thought it had not finished and repeated its last step, and nothing remembered that the first write had happened. 112 occurrences, 88 branches, five years. People were prosecuted over ledgers that agreed with themselves.` Mono narration under the card: `who got hurt, and what nobody had remembered. now the mechanism.`
- 12–30 **watch**: the stage becomes a sequence diagram, three nodes across the top `App · Payments API · Ledger DB`, lifelines, arrows draw one at a time (stroke-dashoffset, ~1.6 s each) with a mono narration line under the diagram changing per step:
  1. App → Payments: `1. POST /pay · key 7f3a · ₹499` — narration `The key travels with the request. The client minted it, once.`
  2. Payments → Ledger: `2. INSERT (key 7f3a, −499) · one transaction` — narration `The key is stored with the result, in the same transaction as the effect.`
  3. Ledger → Payments: `3. committed` — narration `The money moved exactly once. Now the response has to make it back.`
  4. Payments → App, drawn then struck with a red ✕ mid-way: `4. 200 OK · lost` — narration `The signal died here. The client never saw the OK.`
  5. App → Payments: `5. retry · POST /pay · key 7f3a` — narration `The client retries with the same key. That is the whole trick.`
  6. Payments → App: `6. replay stored response · no new row` — narration `Same key: replay the response, not the work.`
- 22–24 **lock**: the diagram unmounts; a dashed `--line-strong` box, `--panel-2` ground: big `That's it. It's gone.` small mono `rebuild it from memory. don't scroll back; there is nothing to scroll back to.`
- 24–32 **rebuild**: a textarea-styled box; Literata text types itself at ~28 chars/s: `The app sends the payment with a key. The server stores the key with the result in the same transaction. When the retry arrives with the same key, it returns the stored result instead of charging again.`
- 32–38 **grade**: a `.score`-style card slides in under the text, header `recall · 4 of 6`, rows tick in 400 ms apart: ✓ `the key travels with the request` · ✓ `key stored with the result` · ✓ `same transaction as the effect` · ✕ `the retention window is how late a retry may safely arrive` · ✓ `replay the response, not the work` · ✕ `the ledger is append-only: inserts replay, updates do not`. Verdict row: `Most of the shape, missing the parts interviewers actually probe.`
- 38–50 **probe**: the score card shrinks to a one-line summary; a transcript column plays lines 700 ms apart, `interviewer` label in `--accent-ink`, `you` in `--ink-3`, your lines in Literata italic:
  - interviewer: `The retry arrives while the first request is still inside the transaction. Not before, not after. During. What does the client see?`
  - you: `…a second charge?`
  - interviewer: `Only if the key is not unique in the database. A unique index on the key: the second insert blocks, then fails, then replays. Where does the guarantee break?`
  - you: `When the effect is outside my database.`
  - interviewer: `Money and email. Stripe accepts your key. Your SMS provider may not.`
- 50–56 **reveal**: the full diagram returns, drawn, small; beside it in Archivo 700 ~3vmin: `where it breaks: effects outside your database.` and under it mono: `kernel · exactly-once delivery does not exist. exactly-once effect does: make the receiver remember what it already did.` Hold. `r · replay` hint.

---

# PERSON B · Rohit Deshmukh (placeholder name; presenter may replace)

Kicker: `PERSON B · ROHIT DESHMUKH · MANUAL QA TESTER → EMBEDDED ENGINEER, SPACE HARDWARE`
h1: `Learns from the failure that caused the invention. Believes it only when his own test passes.`

extracted:
- intake — History first. Needs to know which mission failed and why before he will read how the mechanism works. Stories in, abstractions bounce off.
- retention — Sticks when he breaks it himself. A mechanism he has not tried to break is not learned yet.
- recall — From a failing test. He remembers bugs and reproduction steps, not lectures.
- retrieval mode — Write the test first, then the code, on a simulated board that can actually fail.
- thinking — Bottom-up. Symptom to cause, given / when / then. Five years of QA reflex, now pointed at silicon.
- attention — Long for narrative and anything he can poke. Short for math with no device attached.
- prior knowledge — Test design, edge cases, reproduction. None in C, registers, or electronics. Never soldered.
- calibration — Underconfident. Will not claim to understand until the test goes green; then he over-trusts the green.

generated: **From Test Case to Flight Computer** — every chapter opens with a mission that failed, then the mechanism, then a live simulation, then he writes the test, then the code.
- chapters — Part 1: the computer that flew to the Moon and rebooted on the way down. Part 2: memory, interrupts, timers, and what radiation does to each. Part 3: the flight software stack, test-first.
- interactive diagrams — Register maps and timing diagrams he can step through cycle by cycle; a memory word whose bits he can flip.
- simulations — A simulated MCU: watchdog timer, ECC memory, interrupt latency, brown-out. Every chapter's mechanism runs, and can be made to fail.
- micro-games — "Which mission, which bug": Apollo 11's 1202 alarm, Ariane 5 flight 501's integer overflow, Mars Pathfinder's priority inversion. Match the symptom to the cause before the card flips.
- challenges — Given / when / then. He must write the test that would have caught the historical failure before he sees the fix.
- reels — "A watchdog is a promise to die on time." "Memory that can lie must carry the proof of its own truth." "Radiation does not crash you; it edits you."
- lock & ask — The register map disappears. He writes the init sequence and the test for it from memory; the simulator runs his test.

foot left: `learning-history interview · cognitive task analysis · concrete-before-abstract · worked examples that fade · retrieval by test-writing · failure injection`; foot right: `next: what Rohit experiences`.

## B · experience — chapter `SEU · Single-event upsets: memory that lies`

Kicker: `ROHIT · CHAPTER 9 · SINGLE-EVENT UPSETS · a cosmic ray flips one bit 400 km up. why doesn't the mission end?`
Strip phases: `question · history · mechanism · simulation · lock · test · code · probe`.

Timeline:
- 0–4 **question**: centred Archivo 800 ~5vmin: `A cosmic ray flips one bit in a satellite's memory, 400 km up.` line 2 `--ink-2`: `Why doesn't the mission end?`
- 4–10 **history**: three hairline cards slide in 600 ms apart, mono year + Archivo 700 line + Literata sub:
  - `1969` · `Apollo 11, 1202 alarm` · `The guidance computer overloaded, restarted itself mid-descent, and kept flying. Restart was a feature.`
  - `2003` · `Schaerbeek, Belgium` · `One flipped bit in an electronic voting machine gave a candidate 4,096 extra votes. A single bit, position 13.`
  - `2022` · `Voyager 1` · `Garbled telemetry, 23 billion km away, traced to a corrupted memory chip. Patched by moving the code around it.`
- 10–22 **mechanism**: a memory word drawn as 12 boxes: 8 data bits `0 1 1 0 1 0 1 0` in `--panel-2`, 4 check bits `p1 p2 p4 p8` in `--panel`. Mono caption `hamming(12,8) · 8 bits of data carry 4 bits of proof`. A small filled circle (the particle) drops onto bit 5 (600 ms); bit 5 flips 0→1 and its box turns `--bad-soft`; under the word a line computes: `syndrome = p8 p4 p2 p1 = 0 1 0 1 → bit 5`; then the bit flips back, box turns `--good-soft`, counter `seu corrected · 1`. Narration: `The extra bits let the reader compute which bit lied. One flip: caught and fixed. Two flips: caught, not fixed.`
- 22–34 **simulation**: a board panel, mono, three gauges: `flight counter 0x2A` · `watchdog 1.6 s` · `ecc on`. A ticking counter increments (0x2A, 0x2B…) every 400 ms. At 26 s two particles hit the `program counter` row: `2 bits flipped · uncorrectable` in `--bad`; the counter freezes; the watchdog gauge counts down `1.6 → 0.0` over 1.6 s as a shrinking hairline bar; at zero: `RESET` in Archivo 800 ~4vmin; then `state restored from checkpoint · counter 0x2A · mission continues` in `--good`; the counter resumes.
- 34–36 **lock**: the board and the word disappear; dashed box: `That's it. It's gone.` mono: `write the test first.`
- 36–44 **test**: a code-styled box, mono, lines type in 500 ms apart:
  ```
  given   counter = 0x2A, ecc enabled
  when    bit 5 flips
  then    read returns 0x2A, seu_count == 1
  when    bits 2 and 5 flip
  then    read raises UNCORRECTABLE
  then    watchdog resets the core within 1.6 s
  then    counter == 0x2A after restart
  ```
- 44–52 **code**: beside the test, C types in (mono, ~40 chars/s):
  ```c
  uint8_t ecc_read(addr_t a) {
    word_t w = raw_read(a);
    uint8_t s = syndrome(w);
    if (s) {
      if (!correct(&w, s)) fault_uncorrectable(a);
      seu_count++;
    }
    kick_watchdog();
    return w.data;
  }
  ```
  Under it a `.score`-style line: `tests · 4 of 5 green · failing: watchdog resets the core within 1.6 s` with the failing row in `--bad-soft`.
- 52–60 **probe**: transcript, `mentor` label in `--accent-ink`:
  - mentor: `Your watchdog resets the core. What kicks the watchdog if the code that kicks it is the code that hung?`
  - you (italic): `…nothing. It has to be a timer the CPU cannot stop.`
  - mentor: `Correct. It lives outside the core, on its own clock. That is why your fifth test failed: you kicked it from inside ecc_read.`
  - final line Archivo 700 ~3vmin: `where it breaks: a watchdog kicked from the code it is watching.` mono under: `kernel · memory that can lie must carry the proof of its own truth. a watchdog is a promise to die on time.` Hold. `r · replay`.

---

# PERSON C · Ananya Iyer (placeholder name; presenter may replace)

Kicker: `PERSON C · ANANYA IYER · FRONT-END DEVELOPER → EXOSKELETON CONTROL, DEEP TECH`
h1: `Thinks in state machines and sixteen-millisecond frames. Now the frame is one millisecond and the state is a knee.`

extracted:
- intake — Visual and stateful. She reads a control loop as a state machine with a tick; an equation lands only after she has seen what it moves.
- retention — Sticks when she derives it and then watches it move. Equations without a moving thing evaporate in a day.
- recall — From the picture. She rebuilds the equation from the diagram, not the diagram from the equation.
- retrieval mode — Derive on paper, then tune a simulated joint and watch it fail, then say why.
- thinking — Top-down: "what state are we in?" before "what is the value?". Structure first, magnitude second.
- attention — Long for anything animated or interactive. Short for dense text without a figure.
- prior knowledge — State machines, event loops, animation timing, latency budgets. No mechanics, no control theory; calculus rusty but not gone.
- calibration — Accurate on structure, overconfident on the math. Knows which state the leg is in; misjudges how much torque.

generated: **From the DOM to the Joint** — biomechanics first, then sensors, then the loop as a state machine, then impedance control, then safety, then the papers. Serious by design: the field is.
- chapters — Part 1: the gait cycle as a state machine. Part 2: IMU, encoder, EMG: what the leg can sense in a millisecond. Part 3: impedance control (Hogan, 1985). Part 4: safety before strength. Part 5: reading BLEEX, HAL and the MIT ankle.
- interactive diagrams — The gait cycle she can step through phase by phase with the IMU trace scrolling under it; every transition is a guard she can edit.
- simulations — A one-degree-of-freedom knee with a tunable spring K and damper B; she can make it oscillate, then make it catch.
- micro-games — "What state is the leg in?" from a two-second IMU trace, before the label appears. Streaks, no points.
- challenges — Tune K and B until the knee settles inside 60 ms without overshoot, then explain in one sentence what B did.
- reels — "Stiffness is a spring you can argue with." "The knee is a state machine with a spring in it." "Safety is what you do with a stale number."
- lock & ask — The derivation disappears. She writes the torque law from memory and says what each term does; the simulator runs her law.

foot left: `think-aloud protocol · concept mapping (state machine → control loop) · faded worked examples · dual coding · desirable difficulty · calibration`; foot right: `next: what Ananya experiences`.

## C · experience — chapter `Impedance control · a spring you can argue with`

Kicker: `ANANYA · CHAPTER 11 · IMPEDANCE CONTROL · you step off a curb. your knee catches you before you decide to.`
Strip phases: `question · state · derive · simulate · lock · rebuild · grade · probe`. Serious look: this stage may use the dark palette regardless of theme (set `data-theme="dark"` on the stage panel itself), dense mono, math in Literata italic.

Timeline:
- 0–4 **question**: Archivo 800 ~5vmin: `You step off a curb. Your knee catches you before you decide to.` line 2 `--ink-2`: `How does a powered exoskeleton do that in ten milliseconds without throwing you?`
- 4–16 **state**: left: five hairline state boxes in a row with arrows: `heel strike → loading → mid-stance → toe-off → swing` (swing arrows back to heel strike). Right: an SVG line chart, `shank angular velocity · deg/s` on y, 2 s on x; the trace draws left to right over 8 s; as it passes thresholds the corresponding state box gets the accent outline. Mono narration under: `she knows this shape. it is a state machine with a 1 kHz tick, not a 60 Hz frame. every transition is a guard on the trace.`
- 16–26 **derive**: lines appear 1.2 s apart, Literata italic ~3vmin for math, mono for the gloss:
  - `τ = K (θd − θ) − B θ̇`
  - `K · how hard the joint argues back`
  - `B · how fast it stops arguing`
  - `at heel strike: θd holds, K rises. the joint becomes a spring you can lean on.`
- 26–40 **simulate**: a two-segment stick leg (thigh fixed, shank pivots at the knee) drawn in SVG beside a θ-vs-time chart. Run 1 label `K = 40 · B = 0.5`: on a step input the shank swings and the chart rings (damped sine, 5 visible oscillations), label in `--bad`: `overshoot 38% · throws you`. 1.5 s pause. Run 2 label `K = 40 · B = 4`: the shank settles, the chart is a clean first-order-ish curve reaching the target inside 60 ms, label in `--good`: `settles in 58 ms · catches you`. Mono under: `sense → decide → act: 1 ms. human reflex: 30–50 ms. the exo gets there first, so it must never be wrong.`
- 40–42 **lock**: everything but the strip disappears; dashed box: `That's it. It's gone.` mono: `write the torque law. say what B does.`
- 42–48 **rebuild**: Literata italic types: `τ = K(θd − θ) − Bθ̇. K is the spring, B is the damper. Without B the spring overshoots and the knee rings.`
- 48–52 **grade**: `.score`-style card `recall · 3 of 4`: ✓ `the torque law` · ✓ `K: stiffness` · ✓ `B: damping` · ✕ `θd comes from the gait state, not from the wearer's intent`.
- 52–60 **probe**: transcript, `interviewer` in `--accent-ink`:
  - interviewer: `The IMU drops three samples at heel strike. Your controller now holds a 3 ms stale θ. What does it do?`
  - you (italic): `…it acts on the old angle, so the torque is wrong for 3 ms.`
  - interviewer: `Wrong direction is worse than no torque. Detect the stale sample; freeze τ or fall back to the last safe K. That is chapter 14, safety, and it comes before chapter 15, strength.`
  - final line Archivo 700 ~3vmin: `where it breaks: a controller that trusts a stale number.` mono: `kernel · the knee is a state machine with a spring in it. safety is deciding what to do with a stale number.` Hold. `r · replay`.

---

## Verify before returning (each agent)

Write `reel/tmp-harness-<x>.html` next to nothing else: a minimal page that copies `:root`/`[data-theme=dark]` tokens and the `.slide/.kicker/h1/.lead/.foot` rules from `deck/index.html`, adds the five extra tokens, defines `window.deckAuto = {register(id,h){window.__h=h}}`, includes your fragment, shows the profile slide, and exposes a button-free way to run: `?slide=profile|exp` and on `exp` calls `__h.start(section)`. Then `reel/tmp-shoot-<x>.mjs` (Playwright, import from "playwright", run from `reel/`): 1280×720 and 1920×1080, screenshot the profile slide, then the experience slide at every phase boundary listed above (+300 ms), plus `stop()` then `start()` again to prove replay works, plus one dark-theme profile shot. Assert no scroll on every shot and zero console errors. Read every PNG. Fix. Return: fragment path, screenshot paths, phase timings as implemented, anything from the spec you could not do.
