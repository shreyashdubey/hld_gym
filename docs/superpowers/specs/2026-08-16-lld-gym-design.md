# LLD Gym — Design Spec

Date: 2026-08-16 · Status: approved by user (chat) · Companion to `2026-08-13-hld-gym-design.md`

## What this is

A second self-contained HTML book (`dist/lld/index.html`), served at `/lld` from the
same Vercel project. Low-level design and machine coding, written in Python, built by
the same `build.py` and rendered by the same engine as HLD Gym.

**Its job is distribution.** It is a second free front door that funnels to the same
$39 sprint. It is not a second product, and it does not get its own reps — the sprint
stays HLD-only. Every scope decision below follows from that.

## Why it can exist at all

HLD Gym went from spec commit to 51 chapters authored and verified in **under 13
hours** (`89c60e8` 13 Aug 22:48 → `6b70a30` 14 Aug 11:26). The machine already exists:
`build.py`, `STYLE_GUIDE.md`, the quiz schema, the author→verify agent pipeline, the
Teenage Engineering design system. The marginal cost of a second book is a toc, a
content run, and the machinery in §5.

## Sequencing — this is not the next thing

Shipyard S3 ends 9 September 2026 and the gate is one number: does a stranger pay $39.
As of this spec the sprint is not deployed, the Gumroad product does not exist, and
nothing has been posted. **This book lands after the buy link is live and the first
distribution post is out**, in the window where posting and waiting is not full-time
work. Building it first would be the highest-quality available form of procrastination.

## Decisions, and the reasoning worth keeping

**Aimed at the senior end of LLD, never at beginners.** LLD search traffic skews
SDE-1/SDE-2 and the sprint sells to E5/L5. A book that teaches "what is encapsulation"
pulls traffic that will never buy. The reader is a working developer with ~3 YOE who
can write Python and has never been taught to decompose. Same relationship HLD Gym has
to "what is a load balancer."

**Python, not Java.** Chosen against the market: Indian machine-coding rounds mostly
run in Java, and Python's duck typing hides the contracts SOLID and patterns exist to
teach. Taken anyway because it is the house language across the portfolio (the sprint's
deferred backend is FastAPI) and because the author can verify 46 chapters of it
fluently, which matters more than it sounds when a pipeline is checking the code. Two
mitigations, both required:

- **Types are load-bearing.** `Protocol`, `ABC`, frozen dataclasses, enums, exhaustive
  `match`. The contract a chapter teaches must be visible in the code, not implied by
  convention. A chapter whose design only exists in prose has failed.
- **The book says so out loud.** It states that these rounds mostly run in Java and
  that what transfers is the decomposition, not the syntax. Same honesty move the sell
  page makes about hand-written probes.

**Refactor-driven chapters, over a problem-first spine.** Rejected: mirroring HLD Gym
with a pattern catalogue (competes with ten thousand pages, teaches recognition rather
than judgment, and teaches patterns as a menu — the LLD equivalent of option-listing).
Rejected: pure problem-first (no scaffold, so the same pattern gets re-explained five
times; Bartlett's schema point — material with nothing to attach to slides off).

## The third-change rule

The spine of every chapter, and the guard against the failure mode most pattern books
have:

> One requirement change does not justify a pattern. That is over-engineering, which
> reads junior. Two changes reveal the axis of variation. **Three proves it.** Only
> then does the abstraction get paid for.

So a chapter runs: working code that shipped and is fine → change one, you edit it,
still fine → change two, the edit lands in three places → change three, and the axis
becomes visible → the pattern arrives as the thing that removes the pain → **the price
is stated**, because every pattern buys flexibility with indirection and a book that
hides that teaches cargo cult.

This is `STYLE_GUIDE.md` §1's "problem before solution" rule taken literally, and it
maps onto the actual senior bar, which is not "name the pattern" but "extend this
without rewriting it."

## Content structure (46 chapters)

Chapter ids are `l<part>c<nn>`, distinct from HLD's `p<part>c<nn>`. Titles are chosen
to be queries people type.

**Part 0 — The Meta-Game (2)**
- `l0c01` How the machine-coding round is actually graded
- `l0c02` Company playbooks: Flipkart/Swiggy/Uber India machine coding, Amazon/Microsoft OOD whiteboard, design-review rounds

**Part 1 — Foundations (10)** — taught as failure modes, never as definitions
- `l1c01` Who owns this state?
- `l1c02` Coupling you can feel
- `l1c03` One reason to change
- `l1c04` Open for extension — where the third-change rule comes from
- `l1c05` The inheritance trap
- `l1c06` Interfaces you cannot misuse — `Protocol` vs `ABC` in Python
- `l1c07` Depend on the contract — injection without a framework
- `l1c08` Value objects, and the bugs immutability deletes
- `l1c09` Error design: raise, return, or refuse
- `l1c10` Testability is the evidence — if it is hard to test, the design is wrong

**Part 2 — Patterns Where They're Earned (9)** — named by the pain, so each is a
searched problem and the refactor engine is forced
- `l2c01` When the if-chain keeps growing — Strategy
- `l2c02` When construction gets complicated — Factory, Builder
- `l2c03` When one change must notify many — Observer
- `l2c04` When an object behaves differently in different modes — State
- `l2c05` When you must add behaviour without touching the class — Decorator
- `l2c06` When you need undo — Command, Memento
- `l2c07` When the domain must not know about the database — Repository
- `l2c08` When two interfaces don't fit — Adapter, Facade
- `l2c09` The rest of the catalogue, compressed — explicitly a lookup, not a teaching unit

**Part 3 — Concurrency and Shared State (5)** — where senior is decided
- `l3c01` The race you cannot see
- `l3c02` Locking granularity — one lock, many locks, the wrong lock
- `l3c03` Producer and consumer — bounded buffers and clean shutdown
- `l3c04` Immutability as a concurrency strategy
- `l3c05` The GIL, threads, processes and async — what actually runs in parallel

**Part 4 — The Machine Coding Gauntlet (20)** — full builds, each a query
- `l4c01` Parking lot · `l4c02` Elevator system · `l4c03` Vending machine · `l4c04` ATM
- `l4c05` Splitwise · `l4c06` BookMyShow seat booking · `l4c07` Snake and ladder · `l4c08` Chess
- `l4c09` LRU cache · `l4c10` Rate limiter · `l4c11` Logging framework · `l4c12` Notification service
- `l4c13` Food delivery · `l4c14` Cab booking · `l4c15` Inventory and orders · `l4c16` In-memory file system
- `l4c17` Text editor with undo · `l4c18` Task scheduler · `l4c19` Auction system · `l4c20` Digital wallet

## Chapter anatomy

**Concept chapters (Parts 1–3):** cold open on working code that shipped → change one →
change two → change three, and the axis becomes visible → name the pain → the refactor,
before and after → **what it cost** → `.lens` (how this is probed in the round) →
`.feynman` → exercises, where a fourth requirement tests whether the design absorbs it →
`.takeaways`.

**Gauntlet chapters (Part 4):** scope out loud → core entities → the class design → the
`.crux` → working code → **the extension probe** ("now add X, five minutes") →
concurrency pass → what the interviewer probes next → `.takeaways`.

The extension probe is the third-change rule applied as the exam. Every gauntlet chapter
ends by making the reader's design absorb a change it was not built for, because that is
the round.

**War stories.** LLD has no outage postmortems, but it has a public record of code
decisions with consequences, which is the same organ: the Django class-based views
revolt, `attrs` becoming `dataclasses`, the `asyncio` vs `trio` cancellation argument,
PEPs with published rejected designs, Requests' `Session`, `datetime.utcnow()`
deprecated because the design was a trap. Same rule as HLD: real and verifiable, or pick
a different one.

## Machinery — what is new versus HLD Gym

**1. Code must actually run.** This is the correctness boundary HLD never had: a wrong
war story is embarrassing, a snippet that does not run is fatal, because the reader
pastes it. Chapter HTML contains no code, only a reference that `build.py` inlines:

```html
<figure class="code" data-src="l2c01/strategy_after.py" data-mark="12,18-21">
  <figcaption>The if-chain is gone. Each rate lives with the thing it prices.</figcaption>
</figure>
```

The real file lives at `src/lld/chapters/l2c01.code/strategy_after.py` and ends with an
`assert`-based `if __name__ == "__main__":` self-check. `build.py` executes every code
file with a per-file timeout; a non-zero exit fails the build, at the same loudness as
the existing "every quiz option needs a `why`" check. The page and the tested file
cannot drift, because they are the same bytes.

**2. Highlighting comes from the standard library.** No Prism, no Pygments — `build.py`
imports only `base64, json, re, sys, pathlib` today and that holds. Python ships
`tokenize`, the actual CPython lexer; `build.py` walks tokens and emits
`<span class="tok-*">`. Correct by construction rather than regex-approximate, ~30
lines, Python-only, which is the whole book. A file that will not tokenize is a syntax
error the build catches before the test runs.

**3. Quiz stems carry code.** One optional `"code"` field on a quiz item, highlighted at
build time, rendered in a `<pre>` above the question text. **Options stay plain text** —
code inside a `<button>` is unreadable and `renderQuizItem` sets `textContent`. Note for
the audit pass: a code stem makes the "correct answer is longest" tell easier to trip,
so that check is re-run on this corpus.

**4. The refactor display.** A `<div class="refactor">` wrapping two `<figure
class="code">` blocks, before and after, each captioned, with `data-mark` highlighting
the lines that moved. Stacked, not side-by-side. Side-by-side above 880px is the obvious
upgrade and gets a `ponytail:` note rather than code, because the phone column is where
this book will be read and stacked is correct there anyway.

**5. One script, two books.** `python3 build.py --book lld`, with a `BOOKS` dict holding
source dir, toc path, output path and title. HLD stays exactly where it is
(`src/chapters/`, `src/toc.json`); LLD gets `src/lld/`. Asymmetric on purpose — moving
102 tracked files to make the layout symmetrical churns history for no benefit.
`template.html`, `style.css` and `app.js` are shared unchanged; the code-block CSS ships
in both books and is ~1KB of dead weight in HLD, which is not worth a second stylesheet.

## Build validation

`build.py --book lld` fails on everything it fails on today, plus:

- a `data-src` referencing a code file that does not exist
- a code file that does not tokenize (syntax error)
- a code file whose `__main__` self-check exits non-zero, or times out
- a `.refactor` block missing its before or its after
- a quiz `code` field that does not tokenize

`ALLOWED_DIV` gains `refactor`; `ALLOWED_TAGS` already permits `figure`, `figcaption`,
`pre`, `code` and `span`. The `tok-*` classes are emitted by `build.py` itself, after
validation runs on the authored source, so they never need allow-listing.

## Routes, links, and state

**Routes.** `dist/lld/index.html`, served at `/lld`. `vercel.json` unchanged. Three
surfaces: `/` sells, `/book` is HLD, `/lld` is this.

**The rsync trap — goes in at the same commit as the first LLD build.** `publish:book`
runs `rsync -a --delete --exclude 'book/' --exclude 'reels/' out/ ../dist/`. The moment
`build.py` writes `dist/lld/`, that `--delete` removes it on the next sprint publish.
**`--exclude 'lld/'` is required**, and it is the same class of bug the existing
`--exclude 'book/'` guard exists to prevent.

**Link graph, minimal.** HLD stays the headline book — it is what the sprint grades you
against — so the sell page header is untouched. LLD gets a second link inside the
existing free-book section and one in the footer; no new accent fill, so
`DESIGN-SYSTEM.md` §2.2 holds. Both books carry an `lld` / `hld` entry in the sidebar's
top block beside `home`, not in the header, which already runs out of width at 880px.

**Shared progress, with one fix.** Both books share the `hldgym_v1` localStorage key:
one streak, one XP pool, one rank across both, and no migration. Chapter ids do not
collide, and the engine already handles cross-book state — `dueItems()` skips any
chapter where `isReady()` is false, and `renderHome`'s resume check falls through
safely when `S.lastCh` belongs to the other book.

**`S.boss` is the exception and must be fixed.** It is keyed by bare part number
(`S.boss[p.n]`) and both books have a Part 1, so LLD would silently overwrite HLD's boss
record. Namespace the boss key by book — one line. A second localStorage key would also
work but would split the streak, punishing a reader for studying both books.

## Authoring and verification

Same shape that produced 51 chapters in 13 hours: parallel author agents against the
style guide, verifier agents before merge, `build.py` as the hard gate. Three of the
verifier gates are LLD-specific:

1. **The third-change gate.** Count the requirement changes before the abstraction
   lands. Fewer than three rejects the chapter. A book that introduces Strategy for a
   two-branch `if` teaches the exact over-engineering it claims to cure. This is the
   highest-risk failure mode of the book and it is mechanically checkable.
2. **The price gate.** Every pattern chapter names what the indirection costs. No
   chapter ships with an unpriced abstraction.
3. **The code-is-a-good-example gate.** Passing tests is necessary and not sufficient —
   code can satisfy its asserts and still be a poor demonstration. Needs a design-review
   reader separate from the build.

**Cross-corpus audit, not optional: domain diversity.** Every LLD example on the
internet collapses into payments, shapes, animals and vehicles. A book whose twelfth
chapter is another `PaymentMethod` hierarchy is a bad book. Same discipline as the
war-story differentiation audit already run on HLD.

A `STYLE_GUIDE-LLD.md` carries the contract for authors: the voice rules inherited from
HLD, plus the code-file convention, the third-change rule, the price rule, and the
component list.

## Effort

Machinery is the small half: roughly two hours for `--book`, `tokenize` highlighting,
code inlining, the test runner, and the quiz `code` field. Content is a single-day
pipeline run, slower per chapter than HLD because every snippet must run. Call it
1.5–2 days total.

## Out of scope

Named so nobody rebuilds them later thinking they were forgotten.

- **LLD reps in the sprint.** The sprint stays HLD-only. HLD's terminal skill is drawing
  a system while talking, so its assessment format and target skill are the same object;
  LLD's terminal skill is writing working code, and "rebuild the class diagram from
  memory" trains something that is not the exam. An LLD rep format is an unsolved
  design problem, not a missing feature.
- Multi-language highlighting.
- In-browser code execution. Pyodide is 6MB+ and it is a different product.
- Side-by-side refactor view in v1.
- A second localStorage key, a second stylesheet, a second build script.
