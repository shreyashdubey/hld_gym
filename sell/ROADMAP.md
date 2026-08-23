# Roadmap — will it sell, and what to build for the learner

Written 2026-08-23, from a conversation asking two questions: *will this ever
sell, given free websites, realtime LLM chat and NotebookLM?* and *with
infinite time, what would you improve for the users?* Recorded here so the
reasoning survives the session. Facts below were checked against
`PROGRESS.md` and the Open list as of this date; re-verify before acting on
them later.

---

## Part 1 — the honest sales assessment

**Verdict: it can sell 3 copies. Not on the current trajectory — and free
LLMs are not the reason.**

### The "everything is free now" objection, answered

Information was free before LLMs. The System Design Primer has ~280k GitHub
stars and costs nothing, and people still pay: Alex Xu's books ($40+,
bestsellers), ByteByteGo ($60/yr), Hello Interview premium, interviewing.io
mocks ($150+ per session), NeetCode Pro despite free LeetCode. A buyer with
an onsite in three weeks pays for structure, curation, and being made to
actually do the work — not for information. That market survived free
information; it will survive free chat.

But the objection does kill one pitch: **"an AI interviewer probes you" is
now table stakes.** Anyone can tell ChatGPT or Claude "grill me on caching,
be adversarial" for $0–20/month they already spend. NotebookLM turns the
free book itself into study audio. So the sellable thing is narrower than
the mechanic:

- **LOCK is a commitment device.** A chat never forces you to rebuild from
  memory before showing the answer. Self-directed prompting has roughly zero
  30-day completion; a paid schedule with graded reps is the Duolingo trade,
  and people pay for it despite free everything.
- **Pre-built ground truth.** 197 hand-verified diagrams, rubrics, war
  stories checked against primary sources. An LLM improvises its ground
  truth per session, is sometimes wrong, and the candidate cannot tell.
- **Zero prompt-engineering tax.** The buyer's scarce resource is 17
  evenings, not $19.

That is the moat. Thin but real, and the page already sells mostly this.

### The actual problem

It is in the log, not the market. Form responses: zero — but analytics only
went live 2026-08-22, so nobody knows whether that zero means *came and
declined* (fix the offer) or *nobody came* (fix distribution). The log shows
~8 days of top-decile build work and one line about distribution ("book
posted, venues not recorded"). The reels were built *as* distribution; no
entry says any were ever posted.

**Deadline math:** 3 sales by 9 September at ~0.5–2% cold presell conversion
needs a few hundred *targeted* visitors. One good post of the free book (HN,
r/ExperiencedDevs) can produce that alone — 51 chapters, free, no signup,
sourced war stories is legitimately front-page material. The book is the
distribution asset; it has to actually be distributed, with the sprint line
inside the book closing the loop (still open on the Open list).

**What decides the outcome is whether the remaining days go into
distribution or into a fifth theme.**

---

## Part 2 — with infinite time: improvements ranked by learner value

**Organizing principle: the product's thesis is calibration — the gap
between feeling-of-knowing and actual knowing. Every hour should make that
promise *true*, not add surface.**

### 1. Make the grader real. Everything else is downstream.

Measured (see the LLM-grading item on the Open list): 6/6 on nonsense with
the right vocabulary, **6/6 on a fully reversed read path**, and the three
probe textareas wired to nothing — the learner defends their answer into
/dev/null. Worse than a missing feature: a grader that confirms a wrong
mental model *manufactures* the exact illusion of competence the product
exists to destroy, then sends the learner into the onsite calibrated by a
regex. The design is already on record (Gemini via a route handler, regex
rubric as mandatory fallback, `responseSchema`-pinned output). Days, not
months.

**Force multiplier hiding in the WCAG open item:** write the long
descriptions for all 197 diagrams. The same artifact is (a) the
accessibility fix, (b) per-rep ground truth for the grader, (c) the corpus
for probe generation. One authoring pass, three payoffs.

### 2. Calibration meter — the thing nobody else has.

Before the reveal: "predict your score, 0–6." Store predicted vs actual.
Over 30 days, show the learner their own overconfidence curve shrinking.
That is Roediger & Karpicke turned into a personal instrument — the
restudiers *predicted they would win* and lost, and the product can show
each user their own version of that graph. A chat has no memory of your
miscalibration; NotebookLM cannot do this at all. Novel, cheap, and it
converts the sales-page argument into lived experience.

### 3. Output modes that match the interview.

Standing rule: rep variety is justified by output mode, never input
preference. The interview is **speaking while drawing, defending under
interruption**; the current rep trains typed recall.

- **Draw mode** — rebuild by placing nodes and edges on a canvas, graded as
  a graph. Node/edge ground truth already exists per diagram; the
  playground's BoardContext is half the machinery.
- **Speak mode** — the playground voice loop already works; point it at
  reps, not only free coaching.
- **Defend mode** — probes that follow up on *your* answer, interrupt, and
  push the weak edge. LLM probe generation is the product's stated
  difference; ship it.

### 4. Failure-injection reps.

The kernel rule already demands "a named place it breaks." Rep v2: the
system you just rebuilt — now the cache dies / the lease expires / the
queue backs up. Rebuild the degraded path. Senior loops are decided on
"what breaks at 10×, then what"; the book teaches it, the rep never
exercises it. The 125 war stories are pre-written failure scenarios waiting
to become prompts.

### 5. Spaced return as a real scheduler.

The page promises "spaced return." Build FSRS over the 197 reps, seeded by
grade + calibration error, not fixed intervals. Add **exam-date mode**: a
buyer with an onsite on 15 September gets a schedule compressed toward
their date. Also answers the open "days gated or open?" question with
something better than either option.

### 6. Mock gauntlet mode.

Part 3 is 24 full problems; the playground is a live voice coach. Combined:
a 45-minute mock interview graded against the chapter, unlimited retries —
interviewing.io's $150-per-session product inside a $19 one. The end state
the sprint grows into.

### 7. Narrow diagrams for the book itself.

136 of 197 book diagrams are unreadable on a phone — the device social
traffic lands on, and the book is the distribution. The
`--len`-from-coordinates technique is proven on the sell page's rep and the
log already says it generalises. Grind work, pure user value.

### 8. Close the loop from real interviews.

Post-onsite debrief: which questions came up, where did the candidate
stall → map to chapters → tune probes and gauntlet weighting. Ten users in,
the product is training on the real interview distribution. The wisdom
flywheel; nobody at this price has it.

---

## Non-goals, even with infinite time

More themes (phosphor was the fourth, shipped to zero users), gamification
expansion, social features, more reel polish before any reel has been
posted anywhere. Depth on the loop beats surface every time.

## Sequence when time is finite

1 → 2 → 3-speak (exists; wire it) → 5. **Grader first** — every other
feature routes its value through whether the score can be trusted.

Trust items from the Open list that cost sales while undecided: refund
after 1 September, access mechanism after payment, days gated or open.
Decide and say, in that order.
