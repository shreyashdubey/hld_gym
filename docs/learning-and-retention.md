# Learning and Retention — research notes

Status: discussion note. Nothing built. One decision outstanding at the end.
Date: 2026-08-15

---

## 1. The datum this all rests on

> "even if I read a lot of things + I know a lot of things I can't recall them
> directly from my memory, but the stuff I really know I can draw it, or at
> least the bigger picture"

Not a quirk to work around. It's the encoder reporting what format it stores in.

The storage is **relational** — what sits above what, what flows where, what breaks
when this dies. Text-based recall then asks for that back through a *verbal* cue.
Wrong socket.

The fix isn't "recall harder." It's **make the retrieval cue spatial too**, because
the storage already is.

---

## 2. Why note-taking fails

Transcription is a copy operation. Hand moves, brain idles.

Notes only work when they are **lossy in a way you chose** — when you had to decide
what to throw away. The deciding *is* the comprehension. Lossless notes contain zero
decisions, so they encode nothing.

That's the shared mechanism under all four intuitions:

- teach it to someone
- write it for a 12-year-old
- explain it to someone outside the field
- draw it

Every one is **forced lossy re-encoding under a hard constraint**. A diagram fits only
so many boxes. A 12-year-old holds only so many clauses. The constraint does the work.

### The missing fourth ingredient

None of those four contain it on their own: **feedback**.

Explain something to yourself, feel fluent, never find out you were wrong. From the
inside, fluency is indistinguishable from knowledge. That's why "make notes, then
reread them" fails so reliably — it measures familiarity and calls it mastery.

---

## 3. What actually replicates

Two things work. Almost everything popular doesn't.

### Retrieval practice

Roediger & Karpicke, 2006. One group read a passage four times. Another read it once,
then took three tests on it.

- Measured immediately: rereaders did better.
- Measured a week later: testers crushed them.

**The reversal is the finding.** Pulling knowledge out changes the memory far more than
putting it in again. Every successful recall makes the next one easier. Reading does
nearly nothing to that.

### Spacing

Oldest result in the field — Ebbinghaus, 1885. Same total hours spread across days beats
the same hours in one sitting.

Cepeda's meta-analysis adds the tuning rule: optimal gap scales to how long you want to
keep it, roughly **10–20% of the target retention interval**. Want it in a year? Review
at gaps of a month or two.

### The ranking

Dunlosky et al., 2013 (*Psychological Science in the Public Interest*) scored ten common
study techniques against the evidence. Only two cleared the bar.

| technique | utility |
|---|---|
| Practice testing | **high** |
| Distributed practice | **high** |
| Interleaved practice | moderate |
| Self-explanation | moderate |
| Elaborative interrogation | moderate |
| Summarization | low |
| Highlighting / underlining | low |
| Rereading | low |
| Keyword mnemonic | low |
| Imagery for text | low |

Highlighting and rereading — the two most used study methods on earth — are at the bottom.

---

## 4. Why people choose wrong

Bjork's **desirable difficulties**: conditions that slow you down during practice —
spacing, interleaving, generating before seeing — improve long-term retention *and feel
bad while doing them*.

Rereading feels smooth, so it feels like progress. Learners consistently rate the
inferior method as the better one. That single illusion accounts for most wasted study
time.

Sharpest demonstration: **illusion of explanatory depth**, Rozenblit & Keil 2002. Ask
people how well they understand how a toilet works — high confidence. Ask them to
actually explain the mechanism step by step. Confidence collapses, and their self-rating
afterward drops to match.

Explaining is the diagnostic that exposes the gap. Nothing else does it reliably. The
Feynman instinct is correct and this is the mechanism under it.

---

## 5. What retention actually is: chunking

Chase & Simon, 1973. Show a chess master a real board position for five seconds — they
reconstruct it far better than a novice. Show them a **random** scatter of the same
pieces — the advantage vanishes completely.

Their memory isn't bigger. **Their units are.** Where a novice holds twenty individual
pieces, a master holds four familiar structures.

> Retention isn't storing more items. It's compressing into larger meaningful units —
> and those units form from repeated pattern exposure *with feedback*, never from reading
> a description of the pattern.

A junior sees "load balancer, cache, primary, replica" as four things to remember.
A senior sees "standard read path" as one.

Bartlett supplies the other half — **schema theory**. You remember by fitting new material
onto structure you already hold. Material with nothing to attach to slides straight off.
"I read a lot and can't recall it" almost always means *no scaffold*, not bad memory.

---

## 6. Rest of the toolkit

- **Generation effect** (Slamecka & Graf, 1978) — producing an answer, *even a wrong one*,
  before seeing the right one beats reading the right one cold.
- **Pretesting** — being quizzed on material you haven't studied yet improves how well you
  later learn it. Failing first is productive.
- **Interleaving** (Rohrer & Taylor) — mixing problem types beats blocking them. Teaches
  *which* approach applies, not just how to execute one you were already told to use.
  Learners hate it; it feels chaotic. For system design this is close to the whole skill.
- **Self-explanation / elaborative interrogation** (Chi) — asking "why is this true?" and
  "how does this connect?" while reading. Moderate, reliable, nearly free.
- **Dual coding** (Mayer) — verbal + visual beats either alone, provided they carry the
  same idea rather than duplicating it.
- **Worked examples + expertise reversal** (Sweller) — novices learn more from studying
  worked solutions; experts learn more from solving cold. The optimal method *changes as
  you improve*, so a book taking readers from mid to senior can't hold one format
  throughout.
- **Transfer is the hard problem** — learning in one context mostly fails to carry to
  another. Fix is varied practice across contexts, not more repetition inside one.

---

## 7. How domains that actually manufacture experts do it

| domain | method |
|---|---|
| medicine | See one, do one, teach one. Case-based throughout — never "pneumonia," always a patient. Spaced repetition is near-universal culture now. |
| aviation | Simulators: repeated failure where failure is free. Checklists as deliberate *external* memory — explicit refusal to hold it in the head. |
| military | Drills, then after-action review — a structured retrieval + error-correction ritual, run every time. |
| chess | Study positions, not prose. Tactics puzzles are spaced retrieval on spatial patterns. Closest existing analogue to what this book should be. |
| music | Slow, error-targeted repetition with immediate feedback on every attempt. |
| languages | Comprehensible input + high-volume spaced retrieval. Volume of contact, not volume of explanation. |
| trades | Apprenticeship: produce real artifacts, in front of a critic, from day one. |

Ericsson's **deliberate practice** is the common core of all seven: aimed at a specific
weakness, immediate feedback, repeated, effortful, not especially enjoyable.

Now notice what's absent from that list.

**No domain that seriously produces experts uses reading as its primary mechanism.**
Reading supplies raw material. That is its whole job.

---

## 8. Caution: this is not a learning-styles claim

"Visual learner / auditory learner / kinesthetic learner" is the most popular idea in
education and has no supporting evidence. Pashler's 2008 review found no adequate study
showing that matching instruction to a claimed style helps.

Keep the distinction clean, because the claim here looks superficially similar and is
entirely different:

- *"I prefer visual input"* — a preference about **intake**. This is the debunked one.
- *"What I truly know, I can draw"* — an observation about **output**. Output is evidence
  of encoding.

That's Chase & Simon, not learning styles.

---

## 9. Application to HLD Gym

### Three failures as it stands

1. **Recognition masquerading as recall.** All 1,278 quiz questions are multiple choice —
   the right answer sits there among four. Picking it out leaves a far weaker trace than
   producing it from nothing.
2. **No production.** The reader never makes anything. No artifact, no output, nothing to
   be wrong about — so no feedback can exist.
3. **No spacing that survives.** The review queue is a scheduler, and it's off by default
   on the public site anyway.

### The inversion

Today the book is prose-primary: read 5,000 words, glance at a diagram, answer a quiz.
Flip the primacy.

> **The diagram is the chapter. The prose is the answer key.**

Study a chapter by reconstructing its diagram from a blank slate — place the nodes, draw
the edges, name the arrows — and open the prose only where the reconstruction failed.
Reading stops being intake and becomes debugging.

Constrained reconstruction, not freehand: given the labelled pieces, place and connect
them. Gradeable, spatial, workable on mobile, and it's production rather than recognition.

### The lucky part

This domain hands us something rare. **The terminal skill *is* drawing a system on a
whiteboard while talking through it.** Assessment format and target skill are the same
object. Most subjects have to approximate the real task and hope transfer happens. Here,
practice *is* the performance.

### Overwhelm is a separate, cheaper problem

51 chapters and 284k words don't intimidate because of length. They intimidate because
**the unit of engagement is a chapter** — a commitment with no natural stopping point and
no visible finish. A gym has sets; you always know when a set is done. This book has none.

And nobody reads a 284,000-word book. Say so on the landing page, then hand over a route
through it instead of a wall of contents.

### The constraint that bounds everything

No backend, one static HTML file. So no model-graded free text, no server-side scheduling.
Fine — the strongest available lever is free anyway:

> **Commit before reveal.** Force an answer out of the reader, *then* show the model
> answer. Even a wrong guess beforehand beats reading the answer cold (generation effect).
> Costs nothing to implement.

The Feynman box already exists in the code. Today it's a journal typed into the void. Make
it commit-then-compare and it becomes the second-strongest thing in the book.

---

## 10. Open decision

**Is drawing the assessment, or the medium?**

This is the fork that changes everything downstream. Still unanswered.

**As assessment** — read the chapter as it exists today, then prove you have it by
rebuilding the diagram from blank. Purely additive; all 284k words stay as written.
Cheap, safe, real gains.

**As medium** — the diagram is where you meet the idea *first*, and prose exists only to
resolve what the drawing got wrong. A rewrite of how every chapter opens. Expensive, and
the one I'd actually build.

The deciding question isn't which is more defensible on paper. It's which one you'd
genuinely want to sit down with at 9pm.

---

## Sources referenced

Roediger & Karpicke 2006 · Ebbinghaus 1885 · Cepeda et al. 2006 · Dunlosky et al. 2013 ·
Bjork (desirable difficulties) · Rozenblit & Keil 2002 · Chase & Simon 1973 · Bartlett
(schema theory) · Slamecka & Graf 1978 · Rohrer & Taylor (interleaving) · Chi
(self-explanation) · Mayer (dual coding) · Sweller (worked examples, expertise reversal) ·
Ericsson (deliberate practice) · Pashler et al. 2008
