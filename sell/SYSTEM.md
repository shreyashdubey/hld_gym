# How the system works

Complete reference for the sprint product. If you are a fresh session, read
`CLAUDE.md` first for the read order, then this.

Companion documents:
- `PROGRESS.md` — what has been built, in order, with the reasoning
- `DESIGN-SYSTEM.md` — the visual language ("System Design")

---

## 1. What this is

Two products that share one identity:

| | **HLD Gym** (the book) | **The Sprint** (this repo) |
|---|---|---|
| What | 51 chapters, ~284k words, 197 diagrams, 1,278 questions | 197 reps and 450 reels in 30 days |
| Price | free forever | $19 one-time |
| Role | distribution and the answer key | the thing that produces retention |
| Stack | single self-contained HTML, built by `build.py` | Next.js 16, TSX, static export |
| Where | `src/` + `build.py` at the repo root | `sell/` |
| URL | `/book` | `/` |

**One deployment serves both.** The sprint exports to static files and is copied
into the book repo's `dist/`, which Vercel already serves with
`outputDirectory: dist` and no build command. There is one Vercel project, one
domain, and no second deploy to keep in sync. See §8.

The split is deliberate and load-bearing. **AI made explanation free, which made
forced practice valuable.** Any product whose value is "explains system design
well" now competes with a free chat window that explains anything. So the
explanation is given away, and the paid product is the part a chat window is bad
at: making you produce, remembering what you failed, and refusing to be
agreeable about it.

### The offer, precisely

The sprint covers **the entire book in thirty days**. It is not a sampler, and
the numbers on the page are not chosen for how they sound: every one is derived
from two facts a visitor can verify by opening the free book.

| claim on the page | derivation |
|---|---|
| 30 topics | 51 chapters over 30 days, so one topic is one or two chapters |
| **197 reps** | one per diagram in the book; 197 / 30 = **6 or 7 a day** |
| about an hour a day | 6–7 reps at roughly 7 minutes each |
| **15 reels a day** | 10 on the topic studied that day + 5 on a finished one |
| under 4 minutes | 15 × 15s |
| **450 reels** | 30 × 10 new = 300, plus 30 × 5 revision = 150 |

Two consequences worth stating, because both have already been got wrong once:

1. **A number that cannot be derived does not go on the page.** "30 reps, one a
   day" was the earlier shape and it quietly meant thirty of 197 diagrams: a
   buyer with an onsite in five weeks would have finished the sprint having
   never rebuilt six-sevenths of the book.
2. **Changing the shape changes copy in five places at once** — the hero strip,
   the hero lead, the reels section, the price box list, the `<title>` — plus
   `Reels.tsx`'s own foot note, which lives inside the section that describes it
   and therefore goes stale independently.

### Planned, not built

Five things are wanted and none of them exist. They are written down here rather
than on the page, because the page only sells what ships on 1 September. Their
one public appearance is the reservation form's fifth question, where each is
labelled **planned, not built** — that question is the instrument that decides
which of them is worth building after the first payment.

| | what it is | why it is not first |
|---|---|---|
| **Playground** | a coach you talk to live while you draw. It makes you think aloud, draws alongside you, and unsticks you where you stall, rather than grading you after the fact | the only one that needs realtime audio and a stateful session, so it is the largest build here by a distance |
| **LLM grading** | the recall answer and all three probes graded against the chapter, instead of matched against keywords | designed and parked; the regex rubric stays as the fallback. See the Open list |
| **Reel audio** | ticking under the lease bar, a thud when it empties, a hit on the stale write | additive to a format that is silent-first by spec, so it can land any time |
| **A record dashboard** | every diagram you can and cannot rebuild, over time | needs the backend, which waits for the first payment |
| **LLD gym** | the same loop for low-level design | a second product; spec exists at `../docs/superpowers/specs/2026-08-16-lld-gym-design.md` |

**Playground is the interesting one and also the honest problem.** A live coach
that talks back is the opposite end of the product from the lock: the lock works
by removing help at the moment it would feel best, and a coach is help on
demand. Both can be true in one product — you rebuild alone and get scored, then
take the ones you failed into a session where someone walks you through thinking
aloud — but the sell page must not blur them, because "an interviewer that
pushes back" and "a coach that helps" are opposite promises to a buyer and the
sprint currently sells the first.

Note also what this does to §9 and to the *What you are not buying* section: the
page says **no one-to-one mentoring** and **no mock interview with a human**.
Playground does not contradict either — the coach is software, exactly as the
interviewer already is — but if it ever ships, that copy has to be re-read line
by line rather than left standing.

### How a reservation is taken

There is **no checkout on the site**, and the page says so where the click
happens rather than in small print:

```
CTA (RESERVE_URL) ──► Google Form ──► response lands in the sheet
                      4 questions      │
                      + email          ▼
                                    payment link sent by hand, ≤24h
                                       │
                                       ▼
                                    paid ──► seat, nothing else until 1 Sep
```

The URL lives in `lib/links.ts` and all three CTAs import it: hero, price box,
and the one at the end of the free rep. Each opens in a new tab, because the
form is someone else's page and a visitor who backs out should land on the offer
rather than a blank history entry.

`NEXT_PUBLIC_RESERVE_URL` overrides it and is read **at build time**. Vercel
runs no build for this repo (§8), so setting it in the dashboard does nothing;
it has to be in the environment for `npm run publish:book`. Unset, the constant
in `lib/links.ts` is what ships.

The form is not a waitlist. A waitlist measures curiosity; this asks for the
email *in order to send a payment link*, and its last question asks outright
whether the sender will pay today. See §9 for why that distinction is the whole
point.

### The one question this repo currently answers

> Will a stranger pay $19 for the sprint before it exists?

Everything absent from this repo is absent because it does not serve that
question. See §9.

---

## 2. The rep — the core loop

A rep is the product's unit of work. Not a chapter: a chapter is a commitment
with no natural end, and a gym has sets.

```
   ┌────────┐  click   ┌──────────┐  ~13s   ┌────────┐  submit  ┌────────┐  reveal  ┌──────┐
   │  idle  │ ───────► │ watching │ ──────► │ locked │ ───────► │ graded │ ───────► │ done │
   └────────┘          └──────────┘         └────────┘          └────────┘          └──────┘
   diagram             steps 1..5           SVG unmounts        rubric score        diagram
   frame only          + narration          recall textarea     + 3 probes          returns
```

Implemented as a single `Phase` union in `components/Rep.tsx`:

```ts
type Phase = "idle" | "watching" | "locked" | "graded" | "done";
```

**Phase by phase:**

1. **idle** — the scaffold (nodes and lifelines) boots on arrival, then a pulse
   runs App → Cache → DB on a 3.2s loop with the node it reaches flashing. No
   steps yet. This is the one looping animation on the page and it exists
   because the panel was previously an empty grey rectangle until clicked: the
   most persuasive element on the page, showing nothing. `step` starts at `0`
   rather than `-1`, which is what puts the scaffold on screen — the scaffold
   group is gated on `step >= 0`.

   Copy tells the reader the lock is coming, because being warned and still
   failing is the experience that sells the product.

2. **watching** — five steps reveal on a 2200ms cadence (`STEP_MS`), each with a
   narration line. Total ≈ 11.7s plus a 700ms lead-in. Under
   `prefers-reduced-motion` the whole diagram appears at once and locks after
   1.2s.

3. **locked** — the SVG is **unmounted**, not hidden. Hiding it would leave it in
   the DOM for anyone who opens devtools, and the lock is the product's central
   claim. The panel shutters down over it in 280ms and the verdict stamps in
   behind. A textarea takes focus automatically.

4. **graded** — the six scorecard rows tick in 70ms apart, each mark landing
   160ms behind its own row, verdict last: the reward is the sequence, not the
   number. The answer is scored against the rubric (§4), then three
   follow-ups appear with empty textareas. Model answers are **not rendered**
   until the learner clicks through — commitment before reveal is the generation
   effect, and rendering them hidden would let a curious reader peek.

5. **done** — the model answers appear, and the diagram returns fully drawn so
   the learner can compare it against what they wrote.

### Timing

| constant | value | where |
|---|---|---|
| lead-in before step 1 | 700ms | `Rep.tsx` |
| per-step hold | 2200ms | `STEP_MS` in `lib/rep.ts` |
| arrowhead arm delay | 520ms after its step | `Rep.tsx` |
| line draw duration | 550ms | `.dgDraw` transition |
| node fade | 420ms | `.dgPart` transition |
| lock after last step | +400ms | `Rep.tsx` |
| idle pulse cycle | 3200ms, staggered 300ms per lifeline | `.dgPulse` |
| lock shutter | 280ms | `.locked` |
| scorecard row stagger | 70ms, mark +160ms | `.score li` |

All timers are collected in a ref and cleared on unmount.

---

## 3. The diagram system

### Two variants, one state

`components/Diagram.tsx` exports `DiagramWide` (viewBox `0 0 720 250`) and
`DiagramNarrow` (viewBox `0 0 320 330`). Both are rendered, both receive the
same `step` and `armed` props, and CSS decides which is visible at 720px.

**Why two drawings.** The wide drawing is the book's original, laid out for a
~740px reading column. Rendered into a 297px phone column that is a 0.41 scale,
so its 11px labels arrive at **4.5px**. The narrow variant is redrawn vertically
at viewBox width 320, which on the same phone renders those labels at
**10.2px**.

This is the "narrow grammar" approach from the book's parked mobile-diagram
plan, applied to one diagram. Doing it for 197 diagrams is a project; doing it
for one is an afternoon.

### How the draw-on animation works

Each edge is rendered by a local `Edge` component that computes its own length:

```tsx
const len = Math.round(Math.hypot(x2 - x1, y2 - y1));
// → style={{ "--len": len }}
```

```css
.dgDraw {
  stroke-dasharray: var(--len);
  stroke-dashoffset: var(--len);   /* fully retracted */
  transition: stroke-dashoffset .55s ease, opacity .42s ease;
  opacity: 0;
}
.dgOn .dgDraw { stroke-dashoffset: 0; opacity: 1; }   /* drawn */
```

A step's `<g>` gains `.dgOn` when `step >= n`. That single class drives both the
line draw and the label fade.

> ### ⚠ Do not replace this with `getTotalLength()`
>
> The book measures path length at runtime. That returns **0 for a hidden
> element**, which is precisely why the book's mobile plan concluded a pure CSS
> `display` swap was impossible and a re-render on breakpoint change would be
> needed. Because these are straight lines, the length is just the distance
> between endpoints — so it can be computed without measuring, the hidden
> variant stays correct, and the CSS swap is safe. **This is what makes the
> whole two-variant approach work.**

### The idle pulse, and a second measurement trap

The idle animation is a short bright dash travelling each lifeline, plus a ring
flashing on the node it reaches. Both live inside the scaffold group and run
only while `.stage` carries `.dgIdle` — that class is dropped the moment the rep
starts, because from then on the diagram is saying something and ambient motion
would compete with it.

> ### ⚠ Animate dashes against `pathLength`, never against `var(--len)`
>
> A keyframe value of `calc(-1 * (var(--len) + 26))` **does not interpolate**.
> The browser cannot resolve the custom property at parse time and silently
> falls back to a *discrete* jump, so the pulse teleported to the end of the line
> instead of travelling it. Measured: `strokeDashoffset` went `0px` →
> `calc(-197px)` with nothing in between.
>
> The pulse lines carry `pathLength="100"`, which rescales all dash maths to
> fixed units. The keyframes then hold no variables, and one set drives both the
> 171-unit wide lifeline and the 272-unit narrow one.
>
> Note this is the opposite conclusion from the block above, and both are right:
> `--len` is correct for a *transition* (both endpoints resolve at computed-value
> time) and wrong for a *keyframe*.

### Arrowheads

An SVG marker paints at full opacity regardless of its line's dash pattern, so
an arrowhead would float in mid-air ahead of the line still drawing toward it.
Fix: `markerEnd` is only applied once `armed >= n`, and `armed` is set 520ms
after `step`, just before the 550ms draw completes.

### The specificity trap

```css
.stage svg { display: block; }        /* (0,1,1) */
.dgWide    { display: none; }         /* (0,1,0) — LOSES */
.stage svg.dgWide { display: none; }  /* (0,2,1) — correct */
```

Getting this wrong renders **both diagrams stacked**, and it looks perfectly
fine on desktop because the narrow one is below the fold of the stage box.

---

## 4. The grading rubric

`lib/rep.ts` exports `RUBRIC`: six keys, each a label plus a regex tested against
the learner's free text.

```ts
{ label: "the app writes the cache itself",
  re: /\b(set|sets|writ\w*|fill\w*|populat\w*|puts?|stor\w*|sav\w*)\b/i }
```

**Design rule: match stems, not exact words.** Real answers say "checks",
"writes", "queried". The original `\bcheck\b` marked *"App checks the cache
first"* as a miss — a false negative, in a demo, in front of someone deciding
whether to buy. Being slightly too generous is cheap; being wrong is not.

**Word boundaries still do real work.** `\bdata\b` must not fire on "database";
`\bset\b` must not fire on "dataset". Both cases are pinned in
`lib/rep.test.ts`.

`verdictFor(score, total, blank)` returns the sentence under the scorecard.
The blank case is handled separately and deliberately — leaving it empty is the
most common outcome and the copy treats it as the honest result, not a failure.

**Scoring is presentational, not gated.** Nothing is blocked by a low score. The
scorecard exists to make the gap legible, which is the entire pitch.

---

## 5. Viewer preferences

Two controls in the header, both defined in `lib/prefs.ts` and both following
the same shape — an ordered list of values, a name per value, a `localStorage`
key, and a `data-` attribute on `<html>`.

| control | values | attribute |
|---|---|---|
| theme | Paper `◐`, Blueprint `◑`, Manim `π` | `data-theme` |
| text size | Normal, Large, Largest | `data-fs` |

Both are identical to the book's, on purpose: switching between the two products
should not feel like switching products.

### Text size

`--fs` is a single multiplier (1 / 1.13 / 1.28) and every reading-text rule is
`font-size: calc(Npx * var(--fs))`. One number, ~35 rules, no per-level
stylesheet. **A bare `px` in prose is a bug** — it will be the one line that
refuses to grow.

Two deliberate opt-outs:

- **The header does not scale.** The size control lives in it, and a button that
  resizes itself on click walks out from under the cursor. It is also the one
  row with no space to grow on a phone.
- **SVG labels do not scale.** They are sized in viewBox units and already grow
  with the drawing; multiplying again would scale them twice and break the
  narrow diagram's 10.2px budget.

### The three-state theme problem

A viewer is in one of three states, not two:

| state | root attribute | resolved by |
|---|---|---|
| explicit light | `data-theme="light"` | bare `:root` tokens |
| explicit dark/manim | `data-theme="dark"` / `"manim"` | `:root[data-theme=…]` |
| system default | **nothing stamped** | `prefers-color-scheme` |

So the cascade is ordered:

```css
:root { /* complete light palette */ }

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { /* dark tokens only */ }
}

:root[data-theme="dark"]  { /* dark tokens  */ }
:root[data-theme="manim"] { /* manim tokens */ }
```

Two rules that follow from this:

- **Never define a colour only inside a media or `[data-theme]` block.** It will
  be undefined in the unstamped state.
- **The manim block must redefine every token the dark block sets.** On a dark
  OS with `data-theme="manim"`, the media block still matches (manim ≠ light)
  and applies dark tokens first; manim overrides them by source order at equal
  specificity.

### Avoiding the flash

`PREFS_INIT_SCRIPT` in `lib/prefs.ts` is inlined into `<head>` by
`app/layout.tsx`. It runs before first paint, reads `localStorage`, falls back to
`prefers-color-scheme` for the theme and to `m` for text size, and stamps both
`data-theme` and `data-fs` onto `<html>`. `suppressHydrationWarning` on
`<html>` covers the attribute the server did not render.

### Why `useSyncExternalStore`

By the time React runs, the DOM already holds the theme. React does not own it.

- `useState` + `useEffect` → trips `react-hooks/set-state-in-effect`, and either
  flashes the wrong glyph or mismatches on hydration.
- `useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot)` → reads the
  DOM as the source of truth. `getServerSnapshot` returns `null`, so the server
  emits a neutral placeholder and React swaps in the real glyph after hydration.

`components/Toggles.tsx` keeps **one store per attribute**, memoised in a module
map and created once rather than per render, so `useSyncExternalStore` gets
stable references instead of resubscribing on every render. `set` writes the DOM,
writes `localStorage` (wrapped in try/catch for private mode) and notifies.

---

## 6. Rendering model

| | where it runs |
|---|---|
| `app/layout.tsx` | server — fonts, metadata, prefs init script |
| `app/page.tsx` | server component — all static copy |
| `components/Rep.tsx` | `"use client"` — the state machine |
| `components/Diagram.tsx` | `"use client"` — imported by Rep |
| `components/Toggles.tsx` | `"use client"` — theme + text size |
| `components/StudyChart.tsx` | `"use client"` — draws on scroll into view |
| `components/BookButton.tsx` | `"use client"` — fills on scroll into view |
| `components/FreeBookFab.tsx` | `"use client"` — the phone floater |

The route is statically prerendered (`○ (Static)` in build output). The only
client JavaScript is the rep loop, the two header toggles, and three small
observers. Keep it that way: everything above the rep is copy, and copy has no
reason to ship as JS.

### A pattern the client components share

None of them hold their reveal state in React. They toggle a class on their own
DOM node from inside the effect. Two reasons, both load-bearing:

- **It degrades correctly.** The undrawn state lives behind a class that only
  JavaScript adds (`.chartArm`), so with JS off, or if an observer never fires,
  the statically rendered markup shows the finished element rather than a blank
  one.
- No `setState` in an effect means no `react-hooks/set-state-in-effect` to work
  around.

`StudyChart` arms itself, then observes **one frame later** via
`requestAnimationFrame`: an element already on screen at mount would otherwise
get both classes in the same frame and the transition would have nothing to
interpolate from.

### Fonts

`next/font/google` self-hosts Archivo, Literata and IBM Plex Mono at build time.
No runtime request to a font CDN, so no silent fallback and no third-party
dependency on first paint. The book solves the same problem by base64-embedding
woff2 into a single file; this is the same intent by a different route.

---

## 7. Content model

Everything the rep says lives in `lib/rep.ts`, separate from the component:

| export | what it is |
|---|---|
| `REP_TITLE` | the strip label, e.g. `rep 07 · cache-aside read path` |
| `STEPS` | five narration lines, one per diagram step |
| `STEP_MS` | per-step hold |
| `RUBRIC` | six `{ label, re }` scoring keys |
| `PROBES` | three `{ q, a }` follow-ups |
| `verdictFor()` | the sentence under the scorecard |

Adding a second rep means adding a second data module and lifting the diagram
geometry into data as well. **Do not do this before there is a paying customer** —
one rep is enough to sell one rep.

Source of all content: HLD Gym chapter `p1c06`, "Caching: Remember, Don't
Recompute". The probes are drawn from the chapter's own prose (the invalidation
race, the outage-math figcaption), so the model answers are the book's position,
not invented.

### What the reels are for, and which topics get them

The reels are one of the two things being sold, and their claim is specific:
**hard material made easy to consume, not easy material made short.** Anyone can
cut fifteen seconds on "what is a load balancer". The value is the opposite end
of the book — consensus, quorum overlap, isolation levels, clock skew — the
chapters a reader bounces off once and never opens again.

Two rules follow, and they are content rules, not production ones:

1. **Hardest chapters first.** A reel earns its place by covering something the
   reader was avoiding. Ordering the queue by what is easy to animate produces a
   feed of things nobody needed explained.
2. **Simplify the telling, never the claim.** The kernel is the chapter's actual
   position, compressed; if the fifteen-second version is wrong, it is not a
   reel, it is a liability on a page that sells accuracy. The format already
   enforces most of this: one idea, told as something ordinary going wrong, with
   the system vocabulary withheld until the last two seconds.

`../docs/kernels.md` is the source material, and `reel/`'s header comments carry
the five-beat template.

---

## 8. Build, test, deploy

```bash
npm run dev            # localhost:3000 — this app only
npm run build          # static export to out/; must end with ○ (Static)
npm test               # rubric tests, node --experimental-strip-types
npm run lint           # must be clean
npm run publish:book   # build + copy the export into the book repo
npm run preview        # publish, then serve the combined site on :4173
```

`tsconfig.json` sets `allowImportingTsExtensions: true` because Node's type
stripping requires explicit `.ts` on the test's import, and `noEmit` makes that
safe.

### How the two sites become one deployment

The sprint is `output: "export"`, which is possible because the page uses no
server features. `publish:book` copies the export into the book repo:

```
next build && rsync -a --delete --exclude 'book/' --exclude 'reels/' out/ ../dist/
```

- `--delete` keeps stale exports from accumulating in `dist/`.
- **`--exclude 'book/'` is what stops that `--delete` from wiping a 4.6MB book**
  built by an entirely different pipeline. Do not remove it.

The book is safe in the other direction too: `build.py` writes only
`dist/book/index.html` and never clears `dist/`, so a book rebuild leaves the
sprint's files alone. Both directions were checked before being relied on.

Deploying is then `git push` **in the book repo**. Vercel serves `dist` with no
build command, so the sprint's files at the root and the book at `/book` both go
live with no config change.

### Why `/book` 404s under `npm run dev`

`next dev` runs this app only; the book is a file another pipeline builds. A
`predev` script symlinks it in (`public/book`, gitignored), and a **dev-only**
rewrite maps `/book` and `/book/` to `/book/index.html` — necessary because
`next dev` serves `public/` without directory-index resolution. The rewrite is
gated on `NODE_ENV` and dropped by `output: "export"`, so production never sees
it. Use `npm run preview` to check the real thing.

**Before going live:** set `NEXT_PUBLIC_BUY_URL` to the Gumroad link. Until it
is set the buy button is a dead `#buy` anchor **on purpose** — an unwired page
must not look live.

**Payments:** Gumroad is chosen for speed alone (sign up and sell the same day,
USD, works from India, ~10% fees which are irrelevant at three sales). Dodo
Payments is the better long-term rail — merchant of record, onboards Indian sole
proprietors, and Rishabh Goel is on the Shipyard mentor bench.

---

## 9. What is deliberately absent

| absent | why | when to add |
|---|---|---|
| Backend (FastAPI) | nothing to serve until reps exist | after first payment |
| Auth | a login between a visitor and a payment link costs conversions and answers nothing | when reps are per-user |
| Database | no per-user state yet | with the backend |
| LLM interviewer | a hand-written probe set demos the mechanic at zero cost and zero downtime risk | when building the real rep engine |
| Waitlist / email capture | signups measure curiosity; the gate is `≥1 person prepays` | never as a substitute for the payment |
| Checkout on the site | a payment rail is a merchant account, a product page and a webhook, none of which move the one question. A form plus a hand-sent link takes a real payment today | when the volume makes hand-sending the bottleneck |
| Analytics | the metric is payments, and Gumroad reports those | if traffic needs attribution |

**The reservation form is not the waitlist this table forbids.** The difference
is what happens next: a waitlist ends at the email, and this one exists to send
a payment link within 24 hours, with a final question asking outright whether
the sender will pay today. If it ever starts collecting addresses that are not
followed by a link, it has become the thing the row above rules out.

Its fifth question — *which part of this do you most want?* — is the one piece
of research the page does, and it is free because the buyer is already in the
form. Five of its ten options are labelled **planned, not built** (§1), so an
answer is a vote on what gets built after the first payment rather than a
promise that it exists. Labelling them is not optional: the standing rule
against claiming what the product does not do covers the form as much as the
page.

When the backend arrives, the spend instrument's stack ports directly:
FastAPI + Postgres + bcrypt + opaque session token in an httpOnly cookie
(`shipyard3/app/`). Auth is also solved free to 50k MAU by MonoCloud, a Shipyard
partner.

---

## 10. Known limits

- **One rep.** The page says so; do not let it imply the 197 exist.
- **Four reels of 450.** The page says so, in the section that sells the 450 and
  again in `Reels.tsx`'s own foot note. Both say it because both are read.
- **Probes are hand-written.** Stated on the page. The product generates them.
- **Rubric is keyword-based**, and the cost is measured, not estimated: nonsense
  with the right words scores **6/6**, a *fully reversed* read path scores
  **6/6**, and "I don't remember, let me check my notes" scores **4/6**. It
  detects vocabulary, not knowledge. Acceptable for a demo whose job is to
  expose *omission*; not acceptable for the product. LLM grading is designed and
  parked — see the Open list in `PROGRESS.md`.
- **The three probe textareas are not wired to anything.** No `value`, no
  `onChange`; what a visitor types there is never read, and the model answers
  appear regardless. Fix this with the grader, not before.
- **The narrow diagram is hand-laid.** Its labels fit at viewBox 320 (widest ends
  at x=206); a longer label would need re-checking.
- **No `manim` in the book's `prefers-color-scheme` default** — manim is only
  reachable by explicit toggle, in both products.

---

## 11. Where the free book is linked

The book is the distribution, so the page routes to it five ways. None of them
loop, blink or shake — see `DESIGN-SYSTEM.md` §8 for why that was tried and
removed.

| place | treatment |
|---|---|
| header | `free` chip, static |
| hero | text link under the two CTAs |
| its own section | `BookButton`, fills with accent once on first view |
| rep, after grading | outline button beside the buy button |
| footer | plain link |
| phones | `FreeBookFab`, slides up once, then still |

The floater is bounded at both ends: it waits for the hero to leave, and hides
whenever the price box is on screen — two accent fills in one viewport leave the
eye with no primary action.

The book links back: its brand goes to `/`, and its sidebar carries the `home`
entry that the brand used to be the only route to.

---

## 12. File map

```
app/
  layout.tsx          fonts, metadata, inline prefs script
  page.tsx            all static copy (server component)
  globals.css         tokens + every component style
components/
  Rep.tsx             the five-phase state machine
  Reels.tsx           the reel rail, playlist and fullscreen
  Diagram.tsx         DiagramWide + DiagramNarrow + the idle pulse
  Toggles.tsx         theme + text size cycles (useSyncExternalStore)
  StudyChart.tsx      the Roediger & Karpicke slope chart
  BookButton.tsx      free-book button, fills on first view
  FreeBookFab.tsx     phone-only floating book link
lib/
  rep.ts              rep content: steps, rubric, probes, verdicts
  rep.test.ts         rubric tests (npm test)
  prefs.ts            theme + text size constants, pre-paint init script
next.config.ts        static export, trailing slash, dev-only /book rewrite
AGENTS.md             read order and workflow (CLAUDE.md imports it)
PROGRESS.md           dated log of what shipped and why
SYSTEM.md             this file
DESIGN-SYSTEM.md      the visual language
```

The book and the reels live at the repo root:

```
../
  build.py            assembles src/ into dist/book/index.html
  src/                chapters, app.js, style.css, template.html
  dist/               ← Vercel's output directory, serves ALL THREE
    index.html          the sprint (copied by publish:book)
    book/index.html     the book (written by build.py)
    reels/*.mp4         the reel encodes (written by reel/make.sh)
```

`/reels` is an asset directory, not a route: `Reels.tsx` plays
`/reels/reel<NN>-<cut>.mp4`, two encodes per reel because a rendered video
cannot follow the theme the way the rest of the site does (`paper` for light,
`dark` for everything else). Locally `python3 -m http.server` will happily list
that directory; on Vercel a directory with no `index.html` is a 404.
