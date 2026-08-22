# progress log

Running log for the sprint product. **Newest entries at the bottom.**
Every entry answers three things: **what** shipped, **why** it was built that way,
**how** it works. Bugs found on the way are recorded with the symptom, because
the symptom is what a future session will recognise.

Conventions: one entry per unit of work, not per commit. If a change altered a
decision recorded in `SYSTEM.md` or `DESIGN-SYSTEM.md`, say so in the entry and
update that document in the same commit.

---

## 2026-08-15 — project started: pivot from the spend instrument

**What:** new repo `hld-sprint`. The Shipyard S3 project changed from the
quick-commerce spend instrument to a paid practice product on top of HLD Gym.

**Why:** the spend instrument's own research killed its business case —
`shipyard3/09-demand-research.md` found *"information-only cheap subscriptions
have zero existence proofs"*, and ₹499/yr (~$6) sits below the price floor where
AI products retain at all. System-design interview prep has several existence
proofs at 10–50× that price, buyers with deadlines, and USD pricing. Full
three-option comparison and the learning science behind the mechanic:
`shipyard3/11-learning-startup-conversation.md`.

**The shape:** the book stays free forever (it is the distribution); the paid
product is a 30-day sprint of reps. A rep is
`watch → LOCK → rebuild from memory → interviewer probes → graded → spaced return`.

**Constraint that set the scope:** Shipyard ends **9 September 2026**. Across
three seasons and ~32 builders, only two ever got a paying customer, total
disclosed program revenue $450. So the goal is a countable one: **3 paying
customers wins it outright.**

## 2026-08-15 — presell page, scaffold and design

**What:** Next.js 16 (App Router, TypeScript), statically prerendered. No
Tailwind. Teenage Engineering token set ported from the book.

**Why no Tailwind:** the design is a small, opinionated token system — zero
radius, hairlines, one reserved accent. Utility classes fight that rather than
express it, and the CSS was already written.

**Why no backend, no auth, no Railway:** the page exists to measure one thing,
whether a stranger pays $39 before the product exists. A signup measures
curiosity; only a payment measures demand. A login placed between a visitor and
the payment link costs conversions and answers nothing. FastAPI + Postgres get
built after the first payment — the spend instrument's auth stack ports over.

**Fonts:** Archivo / Literata / IBM Plex Mono via `next/font/google`, self-hosted
at build time. No runtime CDN request, so no silent fallback and no third-party
dependency on first paint.

## 2026-08-15 — the rep: a real playable loop, client-side only

**What:** `components/Rep.tsx`, a five-phase state machine —
`idle → watching → locked → graded → done` — driving one hand-built rep for the
cache-aside read path (source: book chapter `p1c06`).

**Why entirely client-side:** no LLM call means no API key, no per-visitor cost,
and nothing to fall over if the page lands on Hacker News. A hand-written
interviewer for one diagram is indistinguishable from a live one on first
contact. The page states this out loud rather than implying the follow-ups are
generated — the product does generate them, and the difference is the product.

**How the teach phase works:** the diagram's five steps reveal on a 2200ms
cadence with narration. Edges draw themselves via `stroke-dashoffset`; each
step's arrowhead is armed 520ms *after* its line starts drawing, because a
marker paints at full opacity regardless of the dash pattern and would otherwise
hang in mid-air ahead of its own line.

**Verified in-browser, not assumed:** steps reveal in order 1→5, narration
tracks, arrowheads lag one beat, lock unmounts the SVG and autofocuses the
recall box, models stay hidden until the learner commits, diagram returns fully
drawn at the end.

## 2026-08-15 — grading rubric + tests

**What:** `lib/rep.ts` holds a six-key rubric matched against free text, plus
`lib/rep.test.ts` (5 tests, `npm test` via `node --experimental-strip-types`).

**Bug found and fixed:** *"App checks the cache first"* scored as a **miss**.
The key was `\bcheck\b`, which does not match "checks". Keys now match stems
(`check\w*`, `writ\w*`, `quer\w*`). A false negative is far more damaging than
being slightly generous — it makes the grader look broken to precisely the
person deciding whether to pay.

**Why tests here specifically:** the rubric is the only real logic on the page
and it is the thing a buyer judges the product by. Tests cover the inflected
forms people actually write and the boundary cases that keep the loose keys
honest ("database" must not satisfy the `\bdata\b` key; "dataset" must not
satisfy `\bset\b`).

## 2026-08-15 — mobile: the diagram is drawn twice

**What:** `components/Diagram.tsx` exports `DiagramWide` (viewBox 720, the
book's original) and `DiagramNarrow` (viewBox 320, redrawn vertically). Both are
always in the DOM, swapped by CSS at 720px.

**Why:** the wide drawing squeezed into a 297px phone column rendered its 11px
labels at **4.5px** — unreadable, on the device most social traffic arrives
from, for the element that *is* the demo. The narrow redraw holds them at
**10.2px**.

**How the swap is safe:** every line carries its draw length as a `--len` custom
property computed from its own endpoint coordinates, never `getTotalLength()`.
This is the detail that matters: a measured length returns **0** on a hidden
element, which is exactly what blocked the CSS-swap approach in the book's
parked mobile-diagram work. Computing from coordinates makes it work, and the
technique generalises to the book's other 196 diagrams.

**Bug found and fixed:** both diagrams rendered stacked. `.stage svg
{ display: block }` has specificity (0,1,1) and beat a bare `.dgWide` (0,1,0)
inside the media query. Swap rules are now qualified `.stage svg.dgWide`. Worth
remembering because it looked completely fine on desktop.

## 2026-08-15 — theme toggle: three themes, matched to the book

**What:** `components/ThemeToggle.tsx` + `lib/theme.ts`. Cycles
Paper `◐` → Blueprint `◑` → Manim `π`, same order, glyphs and names as the book,
persisted to `localStorage` under `hldsprint_theme`.

**Why three and not two:** the book has three, and switching between the two
products should not feel like switching products. The Manim palette is carried
over from the book unchanged.

**How the flash is avoided:** an inline script (`THEME_INIT_SCRIPT`) writes
`data-theme` onto `<html>` in `<head>`, before first paint. Without it the
server-rendered page paints the default palette and jumps when React hydrates.

**Why `useSyncExternalStore` and not `useState`:** React does not own this
value — the DOM does, because the inline script set it first. Reading it into
`useState` inside an effect trips `react-hooks/set-state-in-effect` and, more
importantly, either flashes the wrong glyph or mismatches on hydration.
`getServerSnapshot` returns `null`, so the server renders a neutral placeholder
and React swaps in the real glyph after hydrating.

**Verified:** all three cycle, glyphs and aria labels correct, accent changes
(`#ff5c00` → `#ff6a14` → `#58c4dd`), choice survives reload, and the diagram
nodes and rep tag re-theme with it.

## 2026-08-15 — documentation set

**What:** this file, plus `SYSTEM.md` (how everything works) and
`DESIGN-SYSTEM.md` (the visual language, named **System Design**), plus
`CLAUDE.md` so any future session picks up the workflow without being told.

**Why:** the project is being handed between sessions under a deadline. The
expensive thing to lose is not the code, it is the reasoning behind decisions
that look arbitrary later — why there is no backend, why lengths are hardcoded,
why the rubric is generous.

## 2026-08-15 — the page was unreadable: hierarchy and copy rebuilt

**What:** rewrote `app/page.tsx` and the chrome/typography in `globals.css`.
Header enlarged, theme control relabelled, hero rebuilt around a terms strip,
prose cut by roughly half.

**Why — the actual failure:** the page never said what it sold. The one line
carrying *what it is, when it starts, how much it costs* was `.eyebrow`: **11px,
grey, lowercase, mono** — the least readable text on the page doing the most
important job. The `h1` was a riddle ("Can you rebuild the diagram?"), and price
and date appeared only after ~600 words of essay prose. Every section was three
to four literary paragraphs with nothing scannable in between, so a reader who
skims — which is most of them — got nothing at all.

**How it was fixed:**

- **Terms strip** (`.termbar`, new): `$39 / 30 reps / 1 Sep / 100% refund` as
  large numerals with mono captions, sitting in the hero above the fold along
  with both CTAs. Measured at 1200×900: the hero ends at 616px, so the entire
  offer is visible without scrolling. Reused lower down for the book's totals.
- **Key line** (`.key`, new): one bolded sentence under every heading carrying
  that section's whole point. The page now reads correctly at kicker + heading +
  key line + numbers alone.
- **`h1` states the problem in plain words** instead of asking a riddle, and the
  lead names the mechanic in one sentence.
- **Header**: 46px → 60px, brand 14.7px → 19px, the book link 11px mono grey →
  14px UI-face with a hairline underline so it reads as a link.
- **Theme control**: glyph-in-a-box (`◐`) → glyph + name (`◐ paper`). An
  unlabelled symbol tells nobody what the control does. Name hides below 560px;
  `aria-label` carries it in both states.
- **Step grid** numbered `01`–`06` in accent with the step name at 16px in the
  UI face, instead of 10.5px grey mono.
- **Prose cut**: the Roediger & Karpicke section went from five paragraphs to
  three short ones; the offer bullets and the honesty section were tightened.

**Verified in-browser at 1200px and 390px:** no horizontal overflow, terms strip
falls to 2×2 on mobile, theme name hides, both CTAs reachable above the fold on
a 844px-tall phone, light and manim palettes both correct.

**Documents updated in the same commit:** `DESIGN-SYSTEM.md` §5.6–5.8 for the
three new components and the copy rule they enforce.

## 2026-08-15 — text size control

**What:** a second header toggle cycling text size Normal → Large → Largest,
next to the theme toggle. `lib/theme.ts` became `lib/prefs.ts` and
`components/ThemeToggle.tsx` became `components/Toggles.tsx`, since both files
now hold two preferences rather than one.

**How the scaling works:** a single `--fs` multiplier on `:root`
(1 / 1.13 / 1.28 via `data-fs`), and every reading-text rule in `globals.css` is
`font-size: calc(Npx * var(--fs))`. One number, ~35 rules, no per-level
stylesheet.

**Two deliberate opt-outs, both worth keeping:**

- **The header does not scale.** The size button lives in it, and a control that
  resizes itself on click walks out from under the cursor. The header is also
  the one row with no space to grow on a 390px phone.
- **SVG labels do not scale.** They are sized in viewBox units and already grow
  with the drawing. Multiplying again would scale them twice and break the
  narrow diagram's 10.2px budget.

**Shared store, not two copies:** both toggles read a value React does not own,
so `Toggles.tsx` has one `storeFor(attr, key)` memoised per attribute and a
`useCycle` hook over it. The store is created once rather than per render, so
`useSyncExternalStore` gets stable references instead of resubscribing on every
render.

**Bug found and fixed:** the button glyph rendered as `aa`, not `aA` — the
`.prefBtn` rule lowercases its label, which flattened the whole size cue. The
glyph span now sets `text-transform: none`.

**Verified in-browser:** cycles and wraps m → l → xl → m, body 17px → 19.21px →
21.76px, `h1` 46px → 58.88px, brand fixed at 19px and `.dgTxt` fixed at 13px
across all three, persists to `localStorage`, and at 390px on Largest there is
still no horizontal overflow and the header holds at 60px.

## 2026-08-15 — em dashes removed from all visible copy

**What:** every em dash on the page replaced across `app/page.tsx`,
`app/layout.tsx` (the `<title>`), `components/Rep.tsx` and `lib/rep.ts` (rep
narration, probe model answers). 24 in total. Verified 0 remaining in
`document.body.innerText`; the four left in the repo are code comments, which
are not copy.

**Why it is not a find-and-replace:** the em dash was doing three different jobs
and each needs a different mark. *"It will probably go badly — that is the entire
point"* is two sentences and became two. *"the testers destroyed them — and the
re-readers had been certain"* is a joined clause and took a comma.
*"Chase & Simon, 1973 — chess masters rebuild…"* introduces and took a colon.
Swapping them all for one substitute would have left the copy reading exactly as
machine-written as before.

Labels needed rewriting rather than repunctuating: *"watch the rep — 13s"* became
*"watch the rep · 13s"* (a separator), *"Reserve a seat — $39"* became *"Reserve
a seat for $39"* (a preposition), *"Read the book — free, no signup"* became
*"Read the free book, no signup"*.

**Rule recorded** in `DESIGN-SYSTEM.md` §10 so it holds for copy written later.

## 2026-08-15 — motion pass 1: the rep loop

**What:** three animated moments in the rep, plus two easing tokens. No new
dependency, no runtime download, page still statically prerendered.

**Why not Rive or Lottie, which is what was asked for:** both are runtimes
(~200KB) around hand-authored vector assets. Duolingo has animators making
those; this project has 25 days and no animator, and the assets are the part
that cannot be written as code. The *feeling* was the real request, and it
comes from things responding, not from the file format. It also has to be in
this page's idiom — bouncy cartoon motion on zero-radius hairline geometry looks
broken, while precise mechanical motion on it looks expensive.

**1. The rep panel is alive at idle.** It was a 268px empty grey rectangle until
clicked: the page's most persuasive element showing nothing. The scaffold now
boots on arrival (nodes fade, then the three lifelines draw a beat apart), and a
pulse runs App, then Cache, then DB on a 3.2s loop. `step` starts at 0 instead
of −1, which is the whole fix for the empty box, since the scaffold group was
gated on `step >= 0`.

**2. The lock has weight.** It used to be a bare unmount. The panel now shutters
down over the diagram in 280ms and the verdict stamps in behind it, scaling
1.06 → 1. This is the emotional core of the product and it previously had no
impact at all.

**3. The score arrives as a sequence.** Six rows tick in 70ms apart, each mark
landing 160ms behind its own row, verdict last. Measured mid-cascade: opacities
1.00 / 0.98 / 0.89 / 0.44 / 0.00 / 0.00, which is the visible wave. The reward
is the sequence, not the number.

**Bug found and fixed, worth remembering:** the pulse teleported to the end
instead of travelling. The keyframe target was
`calc(-1 * (var(--len) + 26))`, and a keyframe value containing `var()` cannot
be resolved at parse time, so the browser falls back to a **discrete** jump
rather than interpolating. Measured `strokeDashoffset` going `0px` →
`calc(-197px)` with nothing in between. Fixed with `pathLength="100"` on the
pulse lines, which rescales all dash maths to constant units — so the keyframes
hold no variables, and one set drives both the 171-unit wide lifeline and the
272-unit narrow one.

**Verified in-browser, not assumed:** scaffold boots and settles, pulse
interpolates smoothly across the eased curve (0 → −4 → −16 → −44 → −83 → −102 →
−112) with the three lines 300ms apart, pulse stops dead when the rep starts
(`dgIdle` removed, animation list empty, opacity 0), shutter and stamp fire on
lock, rows cascade on grading.

**`DESIGN-SYSTEM.md` §8 rewritten in the same commit.** The old rule forbade
page-load entrances and looping outright, which is what produced the dead grey
box. The new section says what loosened, why, and keeps the real boundary: no
parallax, no scroll-jacking, no reveal-on-scroll on a paragraph just because it
is there. It also records the two curves, the duration table, the rule that only
one thing may loop at a time, and the `pathLength` gotcha above.

## 2026-08-15 — the idle motion was measurable but not visible

**What:** the ambient pulse got a node flash to go with it, and the travelling
tick got thicker (stroke 2.4 to 4, dash 12 to 18).

**Why:** reported as "can't see any animation" despite every measurement saying
it ran. Both were true. A 2.4-unit stroke in a 720-unit viewBox renders as a
**~2px hairline**, and the segment was only 12% of a 171-unit lifeline: about a
20px tick sliding down a 175px line. That is perfectly legible in a
`getComputedStyle` reading and effectively invisible in peripheral vision, which
is the only way anyone actually looks at an idle panel.

The lesson worth keeping: **"the animation is running" and "the animation is
visible" are different claims, and only the first one is measurable from the
DOM.** Verify motion by pausing it at a chosen frame and looking at the pixels.

**How it was verified this time:** paused every animation in the SVG at
`currentTime = 900` via `getAnimations()` and screenshotted the frame — three
orange ticks staggered down the lifelines, App and Cache borders lit, DB just
starting. A deterministic frame beats trying to catch a moving one.

**Still worth checking on the reporting machine:** an OS-level "reduce motion"
setting kills all of this by design, and would present as exactly the same
symptom.

## 2026-08-15 — dropped the "six minutes a day" claim and the modality framing

**What:** the hero lead and the step-section heading rewritten. Gone: *"So stop
reading. A diagram teaches itself... Six minutes a day, for thirty days."*

**Why the time claim had to go.** It was an invented number, and it was selling
against the buyer. Six minutes x 30 is three hours, which is not senior
interview prep and should not imply it is; the hours go into the book, and the
sprint is the retrieval layer on top. Worse, a small time commitment reads as a
small product. Duolingo can sell "5 minutes a day" at $7/month casual; this is
$39 with an onsite in five weeks behind it. The page now sells the **count and
the outcome**, and says a rep takes as long as it takes.

**Why the modality framing had to go.** "A diagram teaches itself" quietly
promises a visual product, which invites the learning-styles reading — raised
here as "not everyone is a visual learner, some are audio-visual". Learning
styles do not replicate (Pashler et al. 2008: the meshing interaction almost
never appears). System design is diagrammatic the way sheet music is visual: a
property of the subject, not of the audience.

**The real constraint it surfaced, worth keeping for the product:** rep variety
is justified by **output mode matching the interview** — spoken, drawn, written,
defended under questioning — because that is a transfer argument. It is never
justified by input-modality preference. And the calibration phase measures
**knowledge state**, not learning style; calibrating on a variable that predicts
nothing would put the whole product on sand.

## 2026-08-15 — desktop: two widths instead of one, and a real hero layout

**What:** `--shell: 1140px` (how wide the page may be) split from
`--measure: 44rem` (how wide a line may run), and the hero rebuilt as two
columns above 1000px.

**Why:** `.wrap` was `max-width: 780px` — a number chosen for reading prose, then
applied to everything on the page. So the rep panel, a 720-unit drawing and the
most persuasive element there is, was rendering into a 736px column while a
third of a desktop screen sat empty either side. Prose genuinely needs ~70
characters or the eye loses the return sweep; structure has no such limit, and
answering both questions with one number is what made the page feel narrow and
adrift.

**How:** text elements are pinned to `var(--measure)`; everything structural —
the rep, the step grid, the terms strips, the price box — takes the full shell.
`h1` gets its own `17ch`, wider than the measure, because a headline is scanned
in one pass rather than tracked line to line.

**Why the hero needed restructuring, not just widening:** a single column in a
1140px shell is the same page with bigger margins. Above 1000px it is now the
argument on the left at the measure, the terms and both CTAs on the right, level
with the headline — so price, start date and refund are visible beside the
proposition instead of below it. The terms strip stacks in that column; four
cells in 364px would wrap their captions and go ragged.

**Caught while measuring:** the step grid's `auto-fit` fitted **four** columns
into the wider shell, leaving the six steps as a ragged 4 + 2. Pinned to
`repeat(3, 1fr)` above 900px.

**Verified at 390 / 1280 / 1600:** every prose block measures 704px and every
structural block 1096–1140px; hero is one column on mobile and `676px 364px` at
1280; terms strip returns to 2×2 on the phone; no horizontal overflow anywhere.

**`DESIGN-SYSTEM.md` §4 updated in the same commit** with the two-width rule and
the desktop layout note.

## 2026-08-15 — rewrote the Roediger and Karpicke section: it was unreadable

**What:** the "why the diagram disappears" section rewritten with the real
numbers and an explicit chain of reasoning.

**Why:** Shreyash read it and said he did not understand it. That is the whole
verdict — he has more context on this material than any visitor will, so if the
passage loses him it loses everyone. Four specific faults:

- *"the testers destroyed them"* — **"testers" reads as the people running the
  test**, not the group being tested. Genuinely ambiguous on first pass.
- **No numbers.** 40% versus 61% is the entire punch of the study, and it had
  been compressed into the word "destroyed".
- *"the re-readers had been certain they would do better"* — better than whom,
  predicted when? Dangling on both.
- *"You cannot feel fluent about a diagram that is not on the screen"* — a
  conclusion with its middle step missing. Why does removing it help?

**The chain now spelled out in order:** same passage and same total time; one
group read four times, the other recalled three times with no feedback; five
minutes later the readers led; a week later 40% versus 61%, reversed; the
readers had predicted they would win; easy felt like knowing. Then the link to
the product — while the diagram is on screen you cannot separate recognising it
from being able to build it, so taking it away leaves nothing to feel fluent
about.

**Numbers checked before publishing, not recalled:** 40% / 61% at one week is
Experiment 2, SSSS versus STTT, Roediger & Karpicke 2006, *Psychological
Science* 17(3), 249–255. Putting a made-up figure on a sales page is the kind of
error that costs the sale outright — the same mistake as the "six minutes a day"
line two entries up.

## 2026-08-15 — the study section gets a chart, and the column it was missing

**What:** `components/StudyChart.tsx`, a slope chart of Roediger & Karpicke
Experiment 2, in a new `.split` layout beside the prose.

**Why, two problems with one fix:** the prose block sat flush left at 704px
inside a 1140px shell, leaving ~430px of dead space beside every paragraph. And
a page whose entire pitch is *diagrams beat prose for this material* was making
that case in four paragraphs of prose. The empty column is where the evidence
goes.

**What it shows:** at five minutes restudying leads **81 to 75**; at one week
testing leads **61 to 40**. The lines cross, and the crossing *is* the argument
— much harder to hold as four numbers in a sentence. It draws itself on scroll
into view, so the reversal is something you watch rather than parse.

**Numbers checked against the source, not recalled** — the same discipline as
the copy rewrite above. The paper's own PDF would not fetch (expired
certificate), so both intervals were corroborated separately before anything was
plotted.

**Redrawn once, before shipping:** the first version hung series names off the
right of each line, which forced a 440-unit viewBox to hold them. In a 331px
phone column that renders 10.5px type at **~8px** — exactly the failure the
diagrams were split in two to avoid. Names moved to a legend under the plot,
viewBox down to 360, everything inside it. Measured on a 390px phone: 11–12px,
one drawing for both widths, no second variant needed.

**No-JS safety:** the undrawn state lives behind `.chartArm`, a class only
JavaScript adds. With JS off, or if the observer never fires, the statically
rendered markup shows the chart complete rather than blank. The observer is
armed a frame later, because a chart already on screen at mount would otherwise
get both classes in one frame and have nothing to interpolate from.

**`DESIGN-SYSTEM.md` §5.8 added in the same commit** with the legend rule and
the checked-numbers rule.

## 2026-08-16 — one deployment: the sprint ships inside the book's Vercel project

**What:** the sprint is now a static export mounted at `/sprint` inside the
book's existing Vercel project, instead of a second deployment.
`npm run publish:book` builds it and copies it into the book's `dist/sprint/`.

**Why:** only one Vercel deployment is wanted, and the book must not be
disturbed — same URL, same content, same pipeline.

**Why it is safe:** the book is `build.py` writing a single `dist/index.html`,
served statically with `outputDirectory: dist` and no build command. `build.py`
only ever writes that one file (`OUT.parent.mkdir(exist_ok=True)`) — **it never
clears `dist/`** — so `dist/sprint/` survives a book rebuild. Checked before
relying on it. The book's own config, source and output are untouched; the only
change to that repo is a new folder alongside `index.html`.

**How the sprint exports:** `output: "export"` works because the page uses no
server features — it was already `○ (Static)` and all its JavaScript is
client-side. `basePath: "/sprint"` prefixes every asset URL, and
`trailingSlash: true` makes `/sprint/` resolve to `index.html` on a plain static
host.

**Verified by serving the book's `dist/` exactly as Vercel will:** `/` returns
the book (4.5MB, title "HLD Gym"), `/sprint/` returns the sprint, zero failed
requests, fonts self-hosted under `/sprint/_next/`, idle pulse and node halos
animating, chart drawing on scroll, hero two-column, both toggles live.

**False alarm worth recording:** the first check reported the diagram invisible
and the pulse dead. The viewport was still 390px from an earlier mobile test,
where `.dgWide` is `display: none` — and **CSS animations do not run on hidden
elements**, so a hidden variant reports opacity 0 and an empty animation list.
Not an export bug. Check the viewport before believing a measurement like that.

## 2026-08-16 — the sprint takes the root, the book moves to /book

**What:** the sales page is now the site root and the book is at `/book`. Four
routes to the free book on the page — header chip, hero text link, its own
section button, footer — plus a floating one on phones.

**The consequence, stated plainly:** `hld-gym.vercel.app/` is the sales page
now. Anyone with a link to the book's old root lands on the sales page instead.
Nothing deep-links into the book today (checked: no self-references in `src/` or
the built output), so the cost is limited to links shared before this change.

**How, with one line changed in the book:** `build.py`'s `OUT` moved to
`dist/book/index.html` (plus `parents=True` on the mkdir it already did). Its
assembly, validation and output are otherwise untouched — rebuilt after the
change and it still reports *"OK: 51 chapters valid"*. The sprint's `basePath`
came off and it now exports to `dist/` root.

**The publish step protects the book:**
`rsync -a --delete --exclude 'book/' out/ ../jassi-shreyash/dist/`. `--delete`
keeps stale exports from piling up; `--exclude` is what stops that `--delete`
from wiping a 4.6MB book built by a different pipeline. Verified after running:
book still present, both routes serve the right title.

**Attention treatment, since the free book is the distribution:** a `free` chip
that double-blinks in the header, two rings leaving the book button on a
stagger, and a mobile floater that appears once the hero scrolls away and shakes
every five seconds. All measured live: floater hidden at top, visible after
scroll, accent fill with near-black text, ring and shake both running.

**The accent rule needed sharpening rather than breaking.** `DESIGN-SYSTEM.md`
§2.2 now says one primary action is **per screen, not per page** — so the book
button is accent-filled in its own section, an outline beside the buy button in
the rep, and a plain text link in the hero. Two accent fills never share a
viewport. §8 gained an "attention beacons" subsection recording what keeps a
beacon from looking cheap: short beat, long rest, indicator-style blink, rings
that leave rather than pulse in place.

**Lint caught a real one:** the brand link to `/` is now an internal Next route
and had to become `<Link>`. Every `/book/` link stays a plain `<a>` — the book
is a static file from another pipeline, not a page Next knows about.

## 2026-08-16 — /book 404'd on the dev server

**Symptom:** `localhost:3000/book` returned 404 after the root swap.

**Not a production bug.** `next dev` runs only the Next app; the book is a
static file in the sibling repo's `dist/`, which the dev server has never heard
of. Measured side by side: dev gave `/book/ 404` while the real `dist/` layout
gave `/book/ 200`. Worth keeping the distinction — the deploy was correct the
whole time and only the local view was wrong.

**Fixed anyway**, because checking a link locally and getting a 404 is a
papercut that repeats every session:

- `public/book` is a symlink to `../../jassi-shreyash/dist/book`, created by a
  `predev` script (`ln -sfn`, idempotent) and gitignored, so nothing is
  duplicated into this repo or committed.
- That alone was not enough: **`next dev` serves `public/` but does no
  directory-index resolution**, so the symlink answered `/book/index.html` and
  still 404'd on `/book/`, which is the URL every link on the page uses. A
  dev-only `rewrites()` maps `/book` and `/book/` to `/book/index.html`. It is
  gated on `NODE_ENV === "development"` and dropped by `output: "export"`
  anyway, so production is untouched — the static host resolves the directory
  itself.

**Known, harmless cost:** the export follows the symlink and copies a 4.4MB book
into `out/book/`. It never lands, because `publish:book` rsyncs with
`--exclude 'book/'`.

**Also added `npm run preview`** — builds, publishes, and serves the combined
directory on :4173, which is the only way to see locally exactly what ships.

## 2026-08-16 — took the blink and the shake back out

**What:** every looping animation removed from the free-book calls to action.
The header chip is static, the ping rings are gone, the floater no longer
shakes.

**Why:** called out as cheap, and correctly. The page's own rule already said
*"nothing bounces, a bounce reads as a toy"* — that rule got set aside on
request and the result looked exactly as the rule predicted. Looping motion
reads as desperate, which is expensive on a page asking for money, and the eye
filters repeating movement out within seconds, so it costs credibility **and**
stops working.

**What replaced it, keeping the attention:**

- **Solid colour.** An accent block on a paper ground is already the loudest
  thing in the viewport.
- **A number instead of an adjective.** The floater now reads *"51 chapters,
  free"*. A number is a reason and is read faster than a sentence; "free" alone
  is only a claim.
- **One decisive movement on arrival.** `components/BookButton.tsx` fills with
  accent left to right, once, when it first scrolls into view, then holds. The
  floater slides up once, then holds.

**The principle that made this cohere:** the page's motion vocabulary is
*drawing* — the diagram draws itself, the chart draws itself. A button that
fills itself belongs to that language. A button that blinks belongs to a
different, worse one.

**Second problem found while checking the result:** on a phone the floater sat
right beside the orange price box — two accent fills in one viewport, which
§2.2 forbids because it leaves the eye with no primary action. The floater now
watches the price box as well as the hero, and hides whenever the buy button is
on screen. Verified by scroll position: hidden at the hero, shown through the
middle, hidden from the offer down.

**`DESIGN-SYSTEM.md` §8 rewritten** — the "attention beacons" section that
permitted blinks is replaced by one that records why they were removed, so the
same mistake is not re-derived later.

**Loop audit after the change:** the only infinite animations left on the page
are the rep panel's idle pulse and node halos, which are an indicator inside a
component waiting for input, and stop the moment the rep starts. Nothing that
asks for a click loops.

## 2026-08-16 — the book links to the product; named controls carried across

**What (book repo):** the book's header controls now show glyph **plus name**,
matching the sprint (`aA large`, `◐ paper`), and its brand link now leaves for
the sell page instead of the book's own home view.

**Why the brand changed:** the book is the distribution, and it had **no route
to the product at all**. A reader could finish 51 free chapters without ever
learning the sprint exists. The sell page links to the book five ways; the book
linked back zero times.

**What had to be built before that route could be taken:** the brand was the
*only* way to reach the book's own home view — progress, streak, review — since
the sidebar lists parts and chapters and nothing else. Repointing it without a
replacement would have stranded readers away from their own dashboard. Home now
sits at the top of the sidebar above the parts, separated by a rule, because it
is a different kind of destination from a chapter.

**Two things worth keeping from the named controls:**

- The theme glyph deliberately carries **no `font-family`**. Setting it to the
  UI face broke it: Archivo has no U+25D0 and fell back to something with wrong
  metrics, rendering the mark as a sliver. It stays in mono, where those glyphs
  exist.
- `#text-size` sets width, padding and gap at **id specificity**, which outranks
  a plain class selector. The shared metrics had to be restated at `id+class` or
  the two header buttons came out 34px and 44px side by side on a phone.

**Verified as a round trip, not as two separate pages:** book brand goes to the
sell page, the sell page's header link comes back to the book, and the sidebar
home still restores the dashboard with its content intact. Names drop below
880px; no header overflow at 390px.

## 2026-08-16 — documentation audit

**What:** all four maintained documents brought back in line with the code.
`SYSTEM.md` and `README.md` substantially rewritten, `AGENTS.md` rewritten,
`DESIGN-SYSTEM.md` patched.

**Why now:** the last few days changed the shape of the project — a second URL,
a static export, a shared deployment, a preferences system and a motion language
— and the docs still described a standalone Vercel app with one theme control.
Documentation drift is the specific failure this workflow exists to prevent, and
it had happened anyway.

**Method, worth repeating:** grep the live docs for facts known to have changed
(`780px`, `iconBtn`, `lib/theme`, `ThemeToggle`, "stock Next app", "six
minutes") rather than rereading everything looking for staleness. All eight
probes now come back clean.

**`PROGRESS.md` deliberately not corrected.** It is a dated log, so its old
entries *should* still say `780px` and `ThemeToggle` — that is what was true
when they were written. Rewriting a log to match the present destroys the only
record of why things changed.

**What was actually stale:**

- `SYSTEM.md` — no mention of the two-URL split, the static export,
  `publish:book`, the rsync guard, why `/book` 404s in dev, text size, the idle
  pulse, the lock shutter, the scorecard cascade, the three new client
  components, or the `pathLength` rule. §5 was titled "Theming" while covering
  two preferences. File map missing four files.
- `README.md` — said "deploy to Vercel, no config needed; it is a stock Next
  app", which is now wrong in a way that would waste a session.
- `AGENTS.md` — pointed at `hld-gym.vercel.app` as a separate site, and its hard
  rules predated the loop ban, the accent-per-screen rule, the `--fs` rule and
  the rsync guard.
- `DESIGN-SYSTEM.md` — still documented `.iconBtn`, renamed to `.prefBtn` days
  ago, and referenced a §5.10 that did not exist.

**Two rules added to the conformance checklist** because both were broken in
practice this week: nothing that asks for a click may loop, and no two accent
fills may share a viewport *at any scroll position* — the phone floater passed
a static check and failed a scrolling one.

**Also recorded:** verify motion by pausing it at a chosen frame and looking at
the pixels. "The animation is running" is measurable from the DOM; "the
animation is visible" is not. Reporting the first as if it settled the second
cost a round trip this week.

## 2026-08-16 — kernel reels: a renderer, and reel 01

**What:** `reel/` — a standalone renderer that turns one *kernel* into a 13.2s
vertical video. First cut shipped: **"a lock is a statement about the past"**
(fencing tokens, book chapter `p2c03`), at 1080×1920, 60fps, 3.4MB, in both the
dark and manim palettes.

**What a kernel is:** the compressed causal core of a topic — mechanical enough
to run forward, not a fact to recite. "Odd cycle means not bipartite" is the
result; "2-colour it, every edge flips, an odd walk lands on the wrong colour"
is the kernel, and it regenerates the theorem *and* the algorithm. A candidate
only counts if it derives 3+ facts the learner never stored and has a named
place it breaks. 25 of them now exist, one per concept chapter.

**Why video, and why not on the page:** the reel's job is **distribution**, not
conversion. On the sell page it would compete with the playable rep, and two
motions in a viewport means the rep loses — the same rule that killed the
blinking CTA. It goes out as the post that drives traffic; the page keeps the
rep. A poster frame is rendered for the case where it does go on-page.

**Why not an AI video generator:** the asset is 80% exact text and precise
boxes-and-arrows. Generators garble labels, drift geometry between frames, and
are non-deterministic, so iteration is impossible. Reserved use, if any: a
one-second live-action bookend. Nothing technical gets generated.

**Why not Manim:** it isn't installed, it needs a LaTeX toolchain, and it would
be a *second* renderer for a picture this project already draws. The page's own
SVG grammar, tokens and fonts produce a reel that is pixel-identical to the
product — which is the whole sales argument and something a separate pipeline
would quietly lose.

**How:**

```
reel01.html  →  record.mjs (Playwright, frame-stepped)  →  ffmpeg  →  mp4
```

- **The frame is a pure function of `t`.** No CSS transitions, no keyframes, no
  `setTimeout`. `window.seek(t)` computes every opacity, dash offset and colour
  from the clock. That is what makes recording deterministic: `recordVideo`
  captures at whatever rate the page happens to paint, so a slow frame silently
  becomes a dropped one. 792 frames, identical every run.
- **Standalone HTML, not a Next route** — a route under `app/` would be emitted
  by `output: "export"` and ship with the product. This cannot leak.
- **`reel/package.json` is its own package** so Playwright never enters the
  product's dependency tree.
- **The camera push-in is CSS, not ffmpeg.** Rescaling in ffmpeg would soften
  the 1px hairlines; ffmpeg only adds grain and vignette.
- Draw lengths come from endpoint coordinates, same rule as the product.

**`contact.mjs` is the check that mattered.** It shoots the nine beat frames and
tiles them, and reading that sheet caught four things the DOM would have called
working: the token bounced off the fence while still level with the lock service
(travel and rejection were timed independently); both edges left each client
from the same 20px and smeared into the token chip; B's write was never shown
*passing* the gate, so the fence read as "storage stopped accepting writes"; and
`tickB` sat exactly where the gate later appears.

**The safe-zone bug, found in the encoded file and not in the browser:**
captions sat at 85% of the height and the brand at 92%. Reels and Shorts paint
their own chrome over the bottom ~15%, so both would have been covered on the
platform they were made for. Everything now lives between 10% and 80%, which
cost the diagram some size — the stage is narrower than the column to buy that
vertical budget back.

**The load-bearing beat is the pause (4.4–6.6s):** client A dims and blurs, the
lease bar drains, and *nothing else moves*. Every instinct says shorten it. It
is the idea.

**Bug — symptom: "there is only black screen in reel 01."** The file was fine
from ~0.7s on; frame 0 was black, and a paused player shows frame 0. So does
every feed, as the thumbnail, which made this fatal rather than cosmetic.

Cause was in the timeline helper, not the artwork: `raw(t, a, d)` returns
`(t-a)/d`, so a fade that *starts* at 0 still evaluates to 0 at t=0 no matter
how short the duration. `raw` now treats `d <= 0` as "instant, already there",
and the opening card is opaque at t=0 by design — the movement on arrival is
the scaffold building underneath it, not the hook appearing.

**The first fix for this shipped a check that could not fail.** It compared the
frame-0 PNG file size against 20kB on the theory that a black frame compresses
small — but the grain filter pushes a solid black frame past 60kB, so the check
passed on a black frame and reported "frame 0 ok". Replaced with peak luma via
`signalstats` (black + grain ≈ 30, white text ≈ 220, nothing in between).

**And that measurement was silently empty at first**, because `ffmpeg -v error`
suppresses the `metadata=print` line the check parses — so the variable came
back blank and the comparison was reading nothing. It runs at `-v info` and the
empty case now fails loudly. Two rounds of a check that agreed with whatever it
was given: **a guard that has never been seen to fail has not been tested.**

**Commands:** `cd reel && npm install`, then `node contact.mjs` for the beat
sheet and `./make.sh [dark|manim]` for the video (~90s).

## 2026-08-16 — reel 01 rebuilt as a story; the machinery split out

**Symptom that forced it, in the reader's words:** *"the reel 1 is kinda boring
and hard to understand I don't get what it is trying to tell me."* From the
person the reel is aimed at. That is the whole verdict.

**What was wrong:** it opened on a schematic. `client A / client B / lock
service / storage` are four nouns with no stakes attached, so when the two
writers collided there was nothing to lose. It broke the book's own first rule —
**problem before solution, create the pain first** — and it buried its best fact
(*you can be frozen and not know it*) under a box going blurry with the caption
`GC pause · 41s`, which only means something to someone already burned by it.
Thirteen seconds, nine near-identical boxes-and-arrows frames. A diagram that
moved, not a story.

**What it is now:** a hotel keycard. Your key opens your room at 10:42. At 11:03
the front desk gives the room away while you are asleep. Guest B checks in. You
wake, tap the same dead key, and the lamp says **open** — that is the shock, that
nothing refuses you. Then the same picture is relabelled: front desk becomes the
lock service, the key becomes a lease, the door becomes your database.

**The crux is one image: there is no wire between the desk and the door.** Two
stubs and a cross where the connection would be. The desk can revoke your key
all it likes and the door never hears about it — which is exactly why a lock is
a statement about the past, and why only the resource can close the gap. The
cross is planted quietly at 3.6s and only named at 10.3s; a cross that appears
at the moment it is explained reads as an afterthought.

15.0s, 900 frames. Chosen over two alternatives (money-on-the-line, and an
8-second strip-down) because the analogy is what makes it land for a CSE student
and a fifteen-year engineer at the same time — the book's voice rules already
say so.

**Two defects the contact sheet caught, both invisible from the DOM:** guest B's
key rested at x=180 and parked directly on top of the gap, hiding the one image
the reel exists to deliver; and the lamp — the verdict, the whole point — was 36
units wide and unreadable on a phone. The lamp now carries the words `open` and
`denied`, and the verdict outranks the label beneath it.

**Machinery split out** so scenes 02+ cost a scene file rather than a copy:

- `reel.css` — palettes, layout, safe zone, diagram vocabulary
- `reel.js` — easing/window helpers, the edge system, `mount(T, render)`
- `reelNN.html` — geometry and timeline only

`reel.js` autoplays in a normal browser but opts out behind
`window.REEL_NO_AUTOPLAY`, which `preview.html` sets — the preview owns the
clock, and two clocks fight.

**`preview.html` (built by `preview.mjs`, served with `python3 -m http.server`)
is now how reels get reviewed.** VLC on Linux renders these portrait h264 files
as a black rectangle with hardware decoding on; the page plays the scene live,
so no decoder is involved. It scrubs, steps a frame at a time, jumps to any
beat, and toggles the two palettes. **Do not publish reviews as Artifacts** —
the claude.ai account is shared, so anything published lands in a gallery other
people browse. Serve locally instead.

## 2026-08-16 — reels 02–04, a 3× slower pace, and a paper cut

**What:** three more reels against the format reel 01 proved, every clip stretched
to 45s, and a light palette added as a third render.

| reel | told as | the crux image |
|---|---|---|
| 01 · p2c03 | a hotel keycard | no wire between the front desk and the door |
| 02 · p1c10 | three flatmates, a moved dinner | the two dashed sets overlap, and the overlap is a *person* |
| 03 · p2c07 | a coffee counter in a rush | the cup being made belongs to someone who left 4 minutes ago |
| 04 · p1c06 | sticky notes vs a filing cabinet | same event: a slowdown for three notes, data loss for the fourth |

**Pace is one constant.** `mount({base, pace})` stretches the whole clip, and
`render(t)` still receives base time so the timings inside a scene stay readable.
Retiming forty constants by hand is how a scene drifts out of sync with itself.
15s of story now plays over 45s, at 30fps — motion this slow does not need 60,
and it halves the shoot.

**Scenes declare their own beats.** `mount({beats})` is the single source; the
recorder and the preview read them back scaled. No tool holds a second copy of a
timeline that can drift.

**Three cuts, not two.** `paper` is the book's light palette verbatim. A reel is
a rendered file, not a page, so it never adapts to a viewer — each cut is its own
render and you pick the one that suits the feed. The paper cut takes a gentler
grain and vignette: both are darkening operations, invisible on black and obvious
on white, where they read as sensor noise and a dirty scan.

**Bug — symptom: "what is that weird A" (`told = write Â· asked = read`).**
Mojibake. The scene files declare `<meta charset="utf-8">`, but the pages
`preview.mjs` generates began straight at `<title>`, and Python's `http.server`
sends `text/html` with no charset parameter — so the browser fell back to
Latin-1 and read the middle dot's two UTF-8 bytes as two characters. **A
generated page inherits nothing from the file it was generated from.** Fixed in
the generator and verified by scanning all five served pages for `Â`/`Ã`/`â€`.
The mp4s were never affected: their text is pixels long before a browser sees it.

**Four more caught by contact sheets, none visible from the DOM:** reel 03's
queue label was a `<text>` containing its own count as a `<tspan>`, so
relabelling the label deleted the count; reel 03 printed the wait as `495s`,
which is how a server says it and not how a customer does; reel 04 held the desk
red for seven seconds, spending the alarm colour on "empty" so none was left for
the thing actually lost; and every beat marker sat on the *leading* edge of its
fade, shooting the frame before the thing existed.

**Reviewing is `node preview.mjs` then `python3 -m http.server` in `reel/`.**
`index.html` lists every reel; each page plays, scrubs, steps a frame, jumps to a
named beat and cycles the three cuts.

## 2026-08-16 — one repo, and the reel feed goes on the page

**What:** the sell page moved from its own repository into the book's, as
`sell/`. The reel renderer came with it as `reel/`. A reel feed now sits on the
page as the second-biggest thing on it, and the offer sells it.

**Why the split died:** it bought nothing and cost a working directory every
time. Two git histories, two node trees, and a deploy that ran from the repo you
were not editing — the sell page's own `AGENTS.md` had to open with a warning
that pushing it deployed nothing. Three pipelines, one output directory:

```
build.py       ->  dist/book/index.html
sell/          ->  dist/
reel/make.sh   ->  dist/reels/
```

Each writes only its own subtree, which is what makes them safe to run in any
order. `publish:book` keeps `--exclude 'book/'` and gains `--exclude 'reels/'`;
together they are the only thing stopping `rsync --delete` from wiping 4.6MB of
book and every reel encode. The old repository's history is parked at
`~/Desktop/misc-projects/hld-sprint-history.git` and nothing in the tree
references it.

**The feed borrows a habit, deliberately.** Vertical snap, one reel per screen,
`scroll-snap-stop: always` so a hard flick never skips two. The reel in view
plays; every other one pauses, and any reel fully off screen rewinds to zero so
coming back starts the story rather than dropping you into the middle of it.
**Nothing plays until you scroll to it** — a wall of autoplaying video is what
the rest of the internet does and it reads as an ad.

**Encodes swap with the site theme:** `light` gets the `paper` cut, everything
else gets `dark`. Unlike every other part of this site, a video cannot adapt to
its reader — it is a rendered file, so each palette is a separate render. Manim
falls back to the dark cut rather than paying for a third set of files to serve
one toggle. The `<video>` is keyed on the cut: swapping only `src` leaves the
last decoded frame on screen until the new file buffers, which reads as the
theme toggle being broken.

**Two encodes per cut, because they are different jobs.** The master is
1080×1920 with grain, for uploading to a feed that will re-encode it anyway. The
web copy is 720×1280 with the grain dropped entirely and lands at **644KB**
against the master's 17MB — grain is noise by definition, it defeats every
predictor in the encoder, and at that size nobody can see it. The person
downloading it is on mobile data deciding whether to buy.

**The offer, and the line it must not cross:** ten reels a day on your current
topic, plus reels from topics you already finished mixed back in as revision.
The page says twice — in the section and again in the price box — that **four
exist today and the daily ten start on 1 September**. The hard rule stands:
never claim the product does something it does not.

## 2026-08-16 — the reel feed was boxed, small, and full of em dashes

**Symptom, verbatim:** *"why is our reel inside another box it is itself a
box"*, *"there are em dashes across the whole new text"*, *"every text seems to
be very very small in desktop mode I can't read it even in the largest
setting."* Three separate defects, all in the same section, all mine.

**The boxing.** A reel arrives already framed, already captioned, with its own
title card. It was then put inside a bordered slide, inside a bordered rail, so
the page drew three nested rectangles around one object. The video now gets
**one** hairline and nothing else. The rail has no border and no background.

**The size, which was caused by the boxing.** Each slide was a two-column grid,
video on the left and caption on the right, inside a rail that was itself one
column of the section. That left the video 300px wide. The captions are burned
into the file at 1080px, so at 300px they render around **9px**.

**The text-size control cannot fix this and it is worth knowing why.** `--fs`
scales CSS type. These captions are pixels in an mp4. The only lever is how
large the video is drawn, which is why the caption moved *out* of the rail and
now follows the active reel: the video gets the whole column, 430px, and the
captions land at about **13.5px**.

**The em dashes.** Three, in copy written six entries after the entry recording
that every em dash on this page had been removed. They were not repunctuated in
place, for the reason that entry gives: the mark was doing two different jobs. A
list being introduced took a colon; a clause pretending to belong to its
sentence became its own sentence.

**Verified in the browser at 1440px**, not from the DOM: video 430×764, playing,
zero em dashes in `document.body.innerText`.

## 2026-08-16 — the reel column earns its space, and fullscreen

**Symptom:** *"on the right side there is a lot of empty space"* and *"can we
have fullscreen for the reel?"*

**The space was structural, not a spacing bug.** A 9:16 video 764px tall sits
beside a caption three lines long, so the column was always going to be two
thirds empty. Filling it with padding would have been decoration; it now carries
the **whole playlist** instead of the active title alone. Four kernels in a row
is the fastest argument on the page for what the product actually is, and each
row is also the navigation, which retires the four numbered dots that said less.
The active row is marked by an accent rule on its left edge, not a fill: two
accent fills never share a viewport, and the buy button owns that.

**Fullscreen goes on the rail, never the video.** Fullscreening a `<video>`
shows one reel and hands the browser's own chrome the scroll, which ends the
feed at the first reel. Fullscreening the scroll-snap container keeps it: a
wheel or a swipe moves to the next reel in fullscreen exactly as it does on the
page. `.reelRail:fullscreen` drops the aspect ratio for `100vw/100vh` and each
slide becomes `100vh`.

**The button is not rendered where it cannot work.** iOS Safari allows
fullscreen only on a `<video>`, never on a container, so `document.
fullscreenEnabled` is checked and the control is absent rather than dead.

**Both fullscreen values are read with `useSyncExternalStore`, not mirrored into
state.** The first attempt used `useState` plus an effect and tripped
`react-hooks/set-state-in-effect` — the same rule `Toggles.tsx` already exists
to satisfy. Fullscreen is browser state; React does not own it. Both subscribe
functions are module-level constants, because a fresh function identity on every render
makes `useSyncExternalStore` resubscribe on every render.

**Also added:** arrow keys move between reels while the rail has focus. Scroll
snap already does this with a wheel; a keyboard user needed it said out loud.

**Verified in the browser:** clicking playlist row 3 scrolled the rail, started
reel 03, paused the other three and swapped the heading to "Queueing is refusing
slowly."

---

## 2026-08-17 — $19, and the offer says exactly what it is

**What:** the price dropped from $39 to $19, and the offer section was rewritten
to answer, without prose, what a buyer receives, what happens after they click,
and what is deliberately not included. The CTA now points at a Google Form
(`NEXT_PUBLIC_RESERVE_URL`) instead of a Gumroad product.

**Why the form:** there is still no backend and no payment rail wired, and the
hard rule is that nothing gets built until someone pays. A form is the smallest
thing that can take a real reservation today: four questions plus an email, then
the payment link goes back by hand. It also answers more than a checkout would,
because the four questions say who is buying and what they keep failing on.

**Why $19:** three paying customers wins Shipyard, and the metric is whether a
stranger pays at all before the product exists — not the revenue. Halving the
price halves the size of that decision without changing what is being measured.

**The honesty problem the copy had to solve.** A button reading *Reserve a seat
for $19* that opens a Google Form is a claim the page does not honour: nothing
is reserved and nothing is charged. So the flow is stated where the click
happens — a `.hint` under the hero CTA and under the offer CTA — and *What
happens after you click* spells out all three steps: form, emailed link, paid
seat. The section that follows is *What you are not buying*, which names the
book (free), live calls, Discord, mentoring, a certificate, a human mock
interview, and a job guarantee, all absent. A presale is bought on trust, and
the cheapest trust available is telling someone what they do not get.

**Structure:** the offer section grew three `h3` blocks under the pricebox —
what happens after you click (`.grid2`, **three** cells so the row fills; four
left an empty bordered box on desktop), what you are not buying, and the
existing *Straight about what exists today*. The pricebox list gained a sixth
item, lifetime access, because "not a subscription" in the `.per` line was the
only place that had been said.

**Prices in prose were changed too**, not just the four in the markup:
`README.md`, `SYSTEM.md`, `AGENTS.md`, `DESIGN-SYSTEM.md` and two comments in
`globals.css` all quoted $39 as the reason for a decision ("a bounce reads as a
toy and this page is asking for $39"). This log is history and keeps the old
number.

**Verified in the browser** at 1280 and 390: the three-step row fills one line
on desktop and stacks on the phone, and the `.hint` under the hero CTA wraps to
three mono lines without pushing the free-book line out of the card.

---

## 2026-08-17 — the sprint covers the whole book, and the reel maths is stated

**What:** the shape of the sprint changed from *30 reps, one a day* to *the
entire 51-chapter book in 30 days* — one topic a day, **197 reps** (one per
diagram), **15 reels a day** (10 on today's topic, 5 on a topic already
finished), **450 reels** in total. Contact routes were added at the bottom.

**Why:** one rep a day was thirty diagrams out of 197, so the sprint finished
with six-sevenths of the book never rebuilt. A buyer preparing for an onsite in
five weeks is not buying a sampler. The offer is now the same size as the book.

**The arithmetic, because every number on the page has to survive being
checked by a stranger:**

| claim | derivation |
|---|---|
| 30 topics | 51 chapters over 30 days — one topic is one or two chapters |
| 197 reps | one per diagram in the book; 197 / 30 = **6 or 7 a day** |
| ~1 hour a day | 6–7 reps at roughly 7 minutes each |
| 15 reels a day | 10 new on today's topic + 5 revision from a finished one |
| under 4 minutes | 15 × 15s = 225s |
| 450 reels | 30 × 10 new = 300, plus 30 × 5 revision = 150 |

Every one of those appears on the page, and each is reachable from the two the
reader already trusts: 51 chapters and 197 diagrams, both facts about a book
they can open right now for free.

**Selling the reel number without a wall of prose:** the reels section got a
`.termbar` — `10 / 5 / 15s / 450` — above the copy, the same device the hero and
the book section already use. The strip carries the offer; the paragraphs under
it are for the minority who want the reasoning. The eyebrow became
*15 a day · 450 across the sprint*, which is the whole claim in six words.

**Honesty held.** Four reels exist. The disclosure line under the section now
reads "the daily fifteen start on 1 September; today there are four" rather than
quietly inheriting the old "daily ten". A bigger promise makes the standing rule
*never claim the product does something it does not* more load-bearing, not
less.

**Contact:** a new *Ask me anything before you pay* block above the footer, plus
the same two routes in the footer itself — `shreyashlrn@gmail.com` and LinkedIn.
The pitch is a stranger paying for something that does not exist yet, and the
cheapest reassurance available is a reachable human. The footer became two
`.fact` lines instead of one so the contact routes are not buried inside the
Shipyard credit.

**Also updated:** the page `<title>` and description (they still advertised "30
reps, 30 days"), the CTA at the end of the free rep, and the product tables in
`SYSTEM.md` and `AGENTS.md`.

**Verified in the browser** at 1280: hero strip reads `197 reps / the whole
book`, the reels strip fills one row, and both contact links resolve.

**Two things this entry got wrong, caught by reading the rendered page:**

**Symptom: em dashes were back.** Seven of them, all in copy written that same
day, in a codebase whose §10 rule is *no em dashes anywhere in visible copy* and
which already had one commit dedicated to removing them. Each became the mark
the sentence needed: a comma for an apposition (`197 reps, one for every
diagram`), a colon for an expansion (`450 reels: 300 teaching the book, 150
dragging it back out of you`), a full stop where the clause was really a
sentence. The check is one line and belongs in any review of this page:
`grep -c '—' dist/index.html` must print `0`. Code comments are exempt and stay.

**Symptom: the email and LinkedIn appeared twice within one screen**, once in
*Ask me anything before you pay* and again three lines below in the footer. Two
copies of the same link in one viewport reads as filler, not as availability.
The contact section keeps both routes, and the footer went back to its single
credit line.

**Also stale:** `Reels.tsx`'s own foot note still promised "ten a day … plus
reels from topics you have already finished" and never mentioned the five. Copy
duplicated between a section and the component inside it is copy that goes stale
in exactly one of the two places.

---

## 2026-08-17 — the reservation form is specified, and the docs catch up

**What:** the form behind every CTA now has its exact wording written down in
`README.md`, five questions plus the email. `SYSTEM.md` gained the offer
arithmetic, the reservation flow, and the `/reels` explanation; the page's
step 01 changed from "four questions" to five.

**The fifth question is the interesting one.** *Which part of this do you most
want?*, ten options, five labelled **ships 1 Sep** and five labelled
**planned, not built** — Playground, LLM grading, reel audio, the "what I can
and cannot rebuild" dashboard, and an LLD gym. Nothing else on this page does
roadmap research, and this costs nothing to run because the buyer is already in
the form answering questions about themselves. Which unbuilt option people reach
for decides what gets built after the first payment.

**Playground** is new here and is now written down in `SYSTEM.md` §1: a coach
you talk to live while you draw, that makes you think aloud and unsticks you
where you stall. It is the largest unbuilt thing on the list — realtime audio
plus a stateful session — and it is also the one that argues with the rest of
the product, because the lock works by *removing* help at the moment help would
feel best and a coach is help on demand. Both can hold in one product (rebuild
alone, get scored, then take your failures into a session) but the sell page
cannot blur them while it is selling "an interviewer that pushes back". Recorded
with that tension stated rather than as a feature line, because the tension is
the part a future session will need.

**The labels are not decoration.** *Never claim the product does something it
does not* has so far been enforced on the page; a form that lists four unbuilt
things next to five real ones, unlabelled, breaks the same rule somewhere the
rule had not been applied yet. `AGENTS.md` at the repo root now says the rule
covers the form.

**Q6 sorts the list** — *if I send the payment link today, are you paying $19?*
Three answers: yes, probably, just curious. The whole repo exists to find out
whether a stranger prepays, and asking directly is cheaper than inferring it
from a response count.

**Docs updated in the same pass**, because the last two entries changed things
these files still described the old way:

- `SYSTEM.md` §1 gained **The offer, precisely** (the six-row derivation table,
  every number on the page traced back to *51 chapters* and *197 diagrams*) and
  **How a reservation is taken** (the form-to-payment diagram, plus the
  build-time-only nature of `NEXT_PUBLIC_RESERVE_URL`).
- §9 gained a *Checkout on the site* row, and a paragraph on why the form is not
  the waitlist the table forbids: a waitlist ends at the email, this one exists
  to send a payment link within 24 hours. If it ever stops doing that, it has
  become the banned thing.
- §10 said "do not let it imply thirty exist" and now says 197, plus a second
  limit for four reels of 450.
- §12 was missing `Reels.tsx` entirely, and its `dist/` tree was missing
  `reels/`.

**`/reels` is an asset directory, not a route**, and that is now written down
because it does not look like one locally: `python3 -m http.server` lists it, so
it reads as a stray page. `Reels.tsx` plays `/reels/reel<NN>-<cut>.mp4`, two
encodes per reel, and on Vercel a directory with no `index.html` is a 404.

---

## 2026-08-17 — the form is live and wired, and the reels get their real claim

**What:** `https://forms.gle/hkf5buMLV6PsAomp8` now sits behind all three CTAs.
The URL moved into `lib/links.ts` so the page and the rep import one constant,
each link opens in a new tab, and `NEXT_PUBLIC_RESERVE_URL` still overrides at
build time. The reels section gained the claim that is actually the product's
differentiator.

**`lib/links.ts` exists for a two-line reason:** the rep's closing CTA used to be
an in-page `#buy` jump to the price box, so the URL only appeared once. Now that
all three go to the form, a second copy of the URL is a second thing to forget
when it changes. The old `id="buy"` stays on the price-box CTA — nothing links
to it any more, but external posts might.

**New tab on every reserve link.** The form is someone else's page. A visitor
who opens it, hesitates and backs out should find the offer still there rather
than a blank history entry, and the sell page keeps its scroll position.

**The reels claim, stated properly:** *hard material made easy to consume, not
easy material made short*. Anyone can cut fifteen seconds on what a load
balancer is; the value is consensus, quorum overlap, isolation levels, clock
skew — the chapters a reader bounces off once and never re-opens. The page now
says so in its own paragraph, and `SYSTEM.md` §7 carries the two content rules
that follow: **hardest chapters first**, and **simplify the telling, never the
claim** (a fifteen-second version that is wrong is a liability on a page whose
whole pitch is accuracy).

**Playground** is written up in `SYSTEM.md` §1 alongside the four other unbuilt
things, with the reason it is not first (realtime audio plus a stateful session)
and the copy it would force a re-read of (*no one-to-one mentoring*, *no mock
interview with a human* — both survive, because the coach is software exactly as
the interviewer already is). It reaches the public only as one **planned, not
built** option in the form.

**Two problems with the live form**, both found by reading it rather than
assuming:

1. **It collects no email address.** The entire flow is *form → payment link by
   email*, and the page says so three times. Fix: Settings → Responses →
   Collect email addresses → **Responder input**. Not *Verified*, which forces a
   Google sign-in and so puts a login between a visitor and a payment link, the
   exact thing §9 rules out.
2. **The four unbuilt options in the feature question are unlabelled.**
   Playground, reels with audio, and the LLD gym do not exist. On the page that
   would break the standing rule outright; in a form it is the same claim in a
   quieter place. Each needs `(planned, not built)` in its option text.

## 2026-08-17 — the favicon went back to Vercel's default

**Symptom:** *"the favicon or the google tab icon used to be a beautiful h, now
it is the default stuff vercel gives."*

**Cause:** the book used to own `/`, and `src/template.html` carries its own
favicon as a data URI: an orange square with a white **h**. When the sell page
took the root it brought `app/favicon.ico` from the Next starter, which is the
Vercel mark. Nothing broke; the wrong file simply started winning the root.

**Fix:** `app/icon.svg`, the same square, byte for byte the same artwork as the
book's. Both halves of the site sit at one origin now, so a tab on `/` and a tab
on `/book` must not show different icons. The starter's `next.svg`,
`vercel.svg`, `file.svg`, `globe.svg` and `window.svg` went with it; none were
referenced anywhere.

**White on the orange, not the near-black the header chip uses.** That rule is a
contrast rule, and contrast rules govern text. This is a 16px mark, and parity
with the book beats parity with the chip.

**Bug on the way, worth knowing because it fails silently:** the first version
had a comment explaining the colour choice, and that comment contained a CSS
token name written in its normal form. **XML forbids a double hyphen inside a
comment**, so the file was not valid XML, and a browser renders a malformed SVG
favicon as its default page icon with no error anywhere. It looked exactly like
the bug being fixed. Rendered and looked at the pixels, rather than trusting a
200 on the request.

## 2026-08-17 — the page rebuilt against five critiques

**What:** the sell page was read by five independent reviewers (copy, design,
a sceptical E5 buyer, front-end/SEO/a11y, and the repo's own honesty rule) and
rebuilt against what survived. Every visible section changed; the design system
did not. Word count went from ~1,800 to ~1,900 because the buyer's unanswered
questions were worth more than the cuts, which were made elsewhere.

**Two claims on the page were false, and both were the visitor's to catch:**

- **"15 seconds each" and "under four minutes".** Every encode under
  `dist/reels/` is 45.0s (`PACE = 3`, recorded on 2026-08-16 as "15s of story
  now plays over 45s"), and the reel plays beside the claim. Now `45s` in the
  strip, "about eleven minutes" for the daily fifteen, and `SYSTEM.md` §1
  derives 15 × 45s. Symptom for next time: a number that can be timed must be
  checked against the file, not the spec that wrote it.
- **"A record of what you actually know"** in the price box, while `SYSTEM.md`
  §1 and the form's Q5 both list the record dashboard as *planned, not built*.
  Deleted; the schedule bullet carries the honest half (it remembers what you
  failed).

**Disclosures moved to where the belief forms.** The demo's follow-ups are
declared hand-written *under the probe header in the rep*, with "nothing you
type here is graded"; the keyword score is declared under the verdict. Both used
to live only in a block near the buy button, five screens below the demo, while
the verdict said "the gaps above are where the follow-ups go next" (false: the
probes are fixed) and "this is the normal score" (a norm nobody has measured).
`REP_TITLE` is `p1c06 · …` rather than `rep 07`, which implied six others.
"show me what I missed" is "show what the chapter says", since nothing reads the
textareas. The two closing anchors are sentence case, matching the page's CTAs.
The reduced-motion branch that skipped straight to the lock (1.3s after a
button promising 13s) is gone: the CSS already drops the draw transitions, so
the steps pop in on cadence with their narration. The button's seconds are
derived (`WATCH_S`, 12s), not typed.

**Copy.** Hero lead leads with the mechanic and names the book before calling
it "the whole book"; the fourth strip cell is `~1 hour / a day, 30 days` (the
buyer's first question), refund moves into the hint. Section order is now
hero → rep → how → *why the lock works* → reels → book → offer, so the evidence
sits next to the lock and the reels read as the supporting act. Reels prose is
two paragraphs, rendered inside the playlist column (`<Reels>{children}</Reels>`)
so the proof shows first and the section lost ~500px. Chase & Simon cut. The
book section gained a `.spec` table of the four parts with chapter counts and
compressed topic lists, all checkable in the free book. `125 real outages`
became `125 war stories`, the book's own tag. The offer key and price-box intro
stopped repeating each other. "Straight about what exists today" and "Ask me
anything" merged into **Before you pay**, seven Q&As beside *What you are not
buying* (`.split2`): what exists today, why not a chat window (the §1 thesis,
finally on the page), an interview mid-September (the form asks; the reply says
what the first days cover before payment), falling behind, the refund, why trust
it (judge it by the book, two deep links), contact. Footer carries a plain
reserve link. Title and description carry the brand and name the book.

**Design.** Hero strip 2×2 at desktop (button rises to the headline's second
line); on phones the buttons come before the strip, full width, so the ask is on
the first screen. Wide diagram capped at 880px (labels were 19px, bigger than
body). Price box is a grid: amount and button left, list at the measure right.
Kickers are `--ink-2` (hero excepted) and step numerals `--ink-3`: nine accent
marks in a viewport with nothing to click made the buy button one more orange
thing. `h3` is 20px, above the key line it sits over. Six-step grid is a
hairline list under 560px. `.termbar` carries 18px below; the inline
`marginTop` patches are gone. `--ink-3` light is `#666` (was 4.43:1 on
`--panel-2`). `.chart figcaption` scales with `--fs`. `<main>`, no `<aside>`
around the price, `h3` in the six-step grid so the outline has no skip.

**Verified defects fixed in components:** the reel feed froze after any theme
toggle (videos remount on `key={cut}`, the observer never re-armed: deps are
`[cut]` now); light-theme visitors fetched the dark reel01 before hydration and
then the paper one (`preload` gated on `theme !== null`); the active reel kept
decoding with the rail scrolled off the page (`root: rail` dropped, the
viewport root still clips per-slide); focus after grading landed on the first
probe and scrolled the ticking scorecard off screen (focus the card, scroll it
in); the FAB was tabbable while invisible (`visibility`) and shared a viewport
with the rep's buttons and the book button (it now yields to `.pricebox, .rep,
.bookBtn`). Rail is `role="region"`, space pauses.

**A sixth pass, over the five, found what a closed-document review misses.**
After the demo, the diagram redrew at the top of the panel, 1,000px above the
viewport on desktop and 1,550px on a phone, with a narration ("compare it
against what you actually wrote") nobody saw, and the visitor's own answer had
been unmounted on submit, so there was nothing to compare against. Now the
answer stays, read-only, and the reveal button ("show the diagram again, and
what the chapter says") scrolls the panel back to the diagram: read order is
diagram, your answer, score, the three answers, the CTA. The closing hint was
"the diagram is different every time", which contradicted step 06; it is now
score-aware ("3 of 6. in the sprint a score like that brings this diagram back
within days") with a *run this one again* link, since a second attempt after
reading the answers is the Roediger section's whole thesis and there was no
route to it but reload. Three contradictions the rewrite itself had introduced:
"Six steps per rep" over a five-step demo, "rebuild it six or seven times a
day" reading as one diagram, and `197 reps / the whole book` in the strip beside
*Not the book* in the offer (now `one per diagram`). On phones the reel rail was
a nested scroller with `overscroll-behavior: contain` and `scroll-snap-stop:
always`, nearly full width, so a thumb heading for the offer had to swipe
through four reels; both relax under 860px. `#offer`, `#buy`, `#reels` gain
`scroll-margin-top`, and the hero's text line links to `#offer`. The theme now
crosses the origin: the sell page's init script falls back to the book's
`hldgym_v1` theme before the OS, so a Blueprint reader does not land on a Paper
page.

**The chart mixed two experiments.** Its five-minute pair read 81 / 75, which
are Experiment 1's numbers (one test vs restudy); the one-week pair 40 / 61 is
Experiment 2's. Checked against the PDF this time: Experiment 2 is 83 / 71 at
five minutes and 40 / 61 at one week, and the chart now says so. A chart on a
page asking for money ships only with numbers read off the source, and the
comment that said "checked against the source, not recalled" had been recalled.

**Share card.** `reel/og.mjs` renders `reel/og.html` to `sell/public/og.png`,
1200×630 in the page's own tokens; `layout.tsx` sets `metadataBase`, canonical,
`og:image`, `twitter:image`. `.gitignore` gains `!sell/public/og.png`. Re-run
`node reel/og.mjs` if the h1 or the strip numbers change.

**A verification round, five more independent passes over the rebuilt page**
(rules, code, browser QA with Playwright, buyer, design), and what it changed:
the sprint's score is now stated in *What exists today* ("still matches your
words against the chapter's points, and grading them with a model is planned,
not built"), which is what `SYSTEM.md` §1 and the form's Q5 already said and
the page had not; "hold the line when you argue with it" was cut from the
chat-window answer, since the offer specifies three follow-ups and nothing
about a reply to your defence; "197 reps, one for every diagram" now says "a
first sight of every diagram, and what you failed comes back on top of that",
because a returned diagram is a 198th rep and the two claims contradicted;
"The questions people ask" became "Answered by the person building it", since
nobody has asked yet; the reels wait on their poster under
`prefers-reduced-motion` and play on a click; the poster attribute the SEO
commit added is gated on hydration like `preload`, or a light-theme visitor
fetched four dark posters and then four paper ones; the init script reads
storage in its own `try`, because with cookies blocked it stamped no theme at
all and the reels picked the dark cut on a white page; the marker-defs SVG in
the rep is pinned to 0×0 (`.stage svg { width: 100% }` had stretched it to the
page width); the header's *Read the book* hides "Read the" under 380px instead
of wrapping onto three lines; the footer is outside `<main>` so it is the
contentinfo landmark; and a dozen seams the design pass measured (the price
meta wrapping at largest text, the prompt flush on the lock box, the price
grid stretching its left column, the payment hint hugging the wrong button, the
footer credit wrapping at the measure, three widths of the same button on a
phone, the FAB's footprint over prose, the rep's prose at 130 characters,
`re-opens` breaking at its hyphen). Doc drift caught by the rules pass is fixed
in `SYSTEM.md` (§8's `NEXT_PUBLIC_BUY_URL` paragraph, 13s → 12s, four CTAs, six
book routes, §6/§12 file map), `DESIGN-SYSTEM.md` (accent *actions*, not fills;
the strip is a label; sentence-case CTAs vs lowercase controls; the two non-1px
rules named; caption length) and `AGENTS.md`.

**Not done, and why:** the live Google Form still lists three unbuilt features
unlabelled and is missing six of README's ten Q5 options: a Forms edit, not
code. Refund after shipping is undecided, so the page still says only "if it
does not ship". Naming the payment rail in step 02 waits for the rail to exist.
"The reply … tells you what the first days cover" is a promise the reply has to
keep. Whether days unlock daily or are all open on 1 September is unstated on
the page because it is undecided. The book still has no route to the sprint
except its brand mark and sidebar home: a plain line at chapter end ("Read it;
now rebuild it …") is the highest-leverage edit left, and it belongs to the
book pipeline (`src/app.js` renderChapter and renderHome), which was being
edited in parallel and so was left alone here.

## 2026-08-17 — robots, sitemap, structured data, and the book's missing head

**What:** `/robots.txt`, `/sitemap.xml`, a JSON-LD graph on the root, explicit
robots directives, `theme-color`, and a full head for the book, which had none.

**The book was the gap, and it is the half that matters.** It shipped with
`<title>HLD Gym</title>` and nothing else: no description, no canonical, no
share card. It is 284,000 words of the exact phrases people search for, free and
with no signup, and it was invisible to a crawler beyond two words. It now
carries a descriptive title, a description naming what is actually in it,
`rel=canonical`, the full Open Graph and Twitter set pointing at the same
`og.png` the sell page uses, and two `theme-color` values.

**Two `theme-color` values, not one.** Both halves follow the OS until the
reader picks a theme, so a single value tints the browser chrome the wrong way
for half of them.

**What the structured data deliberately does not say.** No `aggregateRating`,
no `review`: nobody has bought this, so there is nothing to average, and those
two are the most commonly faked properties in the format. The offer is
`PreOrder`, not `InStock`, because it is a presale that ships on 1 September.
The machine-readable version must not quietly claim something stronger than the
visible copy, which says the same thing twice in words.

The graph is `Organization` + `WebSite` + `Book` (with `isAccessibleForFree`)
+ `Product` with one `Offer`. It renders in `<head>` from a server component, so
it costs no client JavaScript.

**No `lastModified` in the sitemap.** It would be re-stamped on every build and
show up as a diff in the committed `dist/` whether or not anything changed. An
untrue lastmod is worse than none.

**Build error worth recording, because the message names the fix:** a metadata
route is a route handler, and under `output: "export"` the build refuses to
prerender one without `export const dynamic = "force-static"`. Both `robots.ts`
and `sitemap.ts` failed with exactly that until it was added.

**Verified on the built output, not asserted:** `/robots.txt` 200 `text/plain`,
`/sitemap.xml` 200 `application/xml` listing both URLs, `/og.png` 200 at
1200×630, JSON-LD parsed back out of the shipped HTML with the offer reading
`19 USD PreOrder`, and every head tag present in `dist/book/index.html`.

## 2026-08-17 — the rest of the SEO surface

**What:** poster frames on the reels, `VideoObject` structured data, a web
manifest, an apple touch icon, a skip link, cache and security headers, and a
fix for a 404 that claimed to be indexable.

**The 404 was arguing with itself.** Next emits `noindex` on it automatically,
and the layout's `index, follow` was inherited on top, so the page shipped both
tags. Crawlers take the most restrictive reading, so nothing was actually
mis-indexed, but a page asserting two opposite things is a bug waiting to be
believed. Robots directives moved to `page.tsx`, which is the page that is
actually indexable; the layout is shared with the 404 and had no business
carrying them.

**Poster frames, which are a UX fix before they are an SEO one.** Three of the
four reels are `preload="none"` and were empty rectangles until scrolled to, and
the first flashed blank while it buffered. Every encode now ships frame 0 as a
17–20KB JPEG. Frame 0 is the hook card, so it gives nothing away — a poster
taken from the end would have shown the kernel, which is the answer.

**`VideoObject` for four reels, not 450.** Structured data describes what is on
the page today. Each carries a summary written for something that cannot watch
it, a thumbnail, a duration and an upload date. `uploadDate` is the date the
files were rendered and is hardcoded: it is a claim about the file, so
re-stamping it every build would make it a lie that also churns the committed
`dist/`.

**Headers, in `vercel.json`.** `/reels/*` and `/_next/static/*` get a year and
`immutable`: both are content-addressed by name, and a repeat visitor was
otherwise re-downloading 7MB of video. `/book/*` gets `must-revalidate` instead,
because it is one 4.5MB file rebuilt in place whenever a chapter changes. Plus
`nosniff`, `Referrer-Policy` and `X-Frame-Options` across everything.

**A skip link.** The book has had one since the WCAG pass; this page did not, so
a keyboard user tabbed the whole header before reaching anything.

**Also:** `manifest.webmanifest` with `display: browser` and no service worker.
There is no offline story worth having here, and a cache that can serve a stale
price is a liability.

**Verified on the built output:** schema parses to four `VideoObject` plus
`Organization`, `WebSite`, `Book`, `Product`; the 404 now carries `noindex` and
nothing else; manifest, apple icon and posters all serve with the right content
types.

## 2026-08-20 — a counter on the door, because zero was unreadable

**What:** `@vercel/analytics` in `app/layout.tsx`, pageviews only. One import,
one component, one paragraph of comment. `SYSTEM.md` §9 loses its Analytics row.

**Why, and it is not "we should have analytics".** The reservation form had zero
responses. The book had been posted and the page had been live since 17 August,
and the site carried no counter of any kind, so that zero had two readings that
demand opposite work: *people came and did not want it* (fix the offer) versus
*nobody came* (fix distribution). Three days of work went into the page in that
blind spot — five verification passes, a design audit, structured data, poster
frames — all of it improving a conversion rate whose denominator was unknown and
might have been zero. §9 said to add analytics "if traffic needs attribution";
the condition had quietly been met.

The paid Vercel usage dashboard was the first thing tried and is paywalled on
this account. Web Analytics is a separate, free-on-Hobby panel, which is why the
package is the answer and the dashboard is not.

**How it survives a repo that builds nothing in the cloud.** `vercel.json` sets
`outputDirectory: dist` with no build command, so an install alone changes
nothing that ships. The loader is baked into a client chunk by the local
`npm run publish:book` and lands in the committed `dist/`. Verified there:
`dist/_next/static/chunks/3dzdqsep0txr3.js` carries the `_vercel/insights` URL,
and the book (4.4MB) and reel encodes (7.0MB) both survived the `rsync --delete`
because the two excludes did their job.

**Verified in a browser, not from the DOM alone.** Served the built `dist/` on
:4173: the script tag is injected at `/_vercel/insights/script.js`, `window.va`
is defined, and `window.vaq` holds exactly one queued event — the pageview,
waiting to flush. That path 404s locally and is the only console error, because
it is a Vercel platform route no static server can answer; it resolves on the
deployment. Lint clean, 5/5 rubric tests, `grep -c '—' 0`.

**Pageviews only, deliberately.** No `track()` on the three `RESERVE_URL` links
yet. A click count is a numerator, and the whole point of this change is that
nobody knows the denominator. Once traffic is a real number, the CTA events are
the next cut and they are three onClick handlers.

**Not done, and it is the half that matters:** Web Analytics has to be switched
on in the Vercel project dashboard. Until that toggle flips, the script 404s in
production exactly as it does locally and collects nothing. This is a click in
Vercel, not a line in this repo.

---

---

## Open

- [ ] **The live form's Q5 has four options, three unbuilt and none labelled**
      (Playground, reels with audio, LLD gym beside the lock), and is missing
      six of README's ten. Email is collected now (Responder input). Google
      Forms edit, no code involved.
- [x] **Reservation form created and wired**
      (`https://forms.gle/hkf5buMLV6PsAomp8`, `lib/links.ts`).
- [ ] **Gumroad product not created.** Not blocking any more: the payment link
      is emailed by hand after a form response, so it only has to exist before
      the first reply goes out.
- [x] **Live at `https://hld-gym.vercel.app/`** (2026-08-17). Book at `/book/`,
      reel encodes serving from `/reels/`, all three CTAs on the form.
- [x] **Free book posted** (reported 2026-08-20; venues not recorded here).
      Whether those posts sent anyone is exactly what the new counter is
      there to answer, and could not be answered before it.
- [ ] **Web Analytics not yet enabled in the Vercel dashboard.** The code
      shipped 2026-08-20; the panel is a toggle in project settings and
      the script collects nothing until it is on. Free on Hobby.
- [ ] **Reels 05+ not cut.** Four exist and play on the page. Each new kernel
      is a new `reelNN.html` against the same five-beat template.
- [ ] **Refund after 1 September is undecided.** The page promises a refund
      only if the sprint does not ship; a buyer who wants out on day five gets
      no answer. Say either "no refund after it ships" or "seven days, reply
      to the payment email"; either is better than silence.
- [ ] **The book does not mention the sprint.** Six routes from `/` to `/book/`,
      one back (the brand mark, plus the sidebar home). The asset that gets
      posted is the book; a plain sprint line at chapter end and on the book's
      home (`src/app.js`, no claim beyond what the page makes) closes the loop.
- [ ] **How is access granted after payment?** "Lifetime access" and "no
      account" are both on the page; the mechanism (a link to the same email,
      a login, something else) is not, and a senior engineer notices. Decide
      with the backend, then say it in step 03.
- [ ] **Days gated or open?** Whether day N unlocks on its date or all thirty
      are open from 1 September is undecided and therefore unsaid; a buyer with
      an onsite on 15 September asks exactly this. Decide, then say it in
      *Before you pay*.
- [ ] **Reel audio unbuilt.** Spec is silent-first with burned captions, so this
      is additive: ticking under the lease bar, a low thud when it empties, one
      sharp hit on the stale write, a crisp click on the rejection. Muted
      playback must still read.
- [ ] Spend instrument not yet publicly killed (the retrospective post — no
      failure retrospective exists across all three Shipyard seasons).
- [ ] FAULT kill-test emails to HUD and Prime Intellect unsent
      (`shipyard3/06-fault-playbook.md` §5 — 30 minutes, still unrun).
- [x] **Playground unspecified.** ~~A live coach that talks while you draw,
      keeps you thinking aloud, and unsticks you. No spec, no chosen stack, no
      cost model for realtime audio.~~ Specified and built:
      `docs/superpowers/specs/2026-08-21-playground-design.md`, implemented
      across thirteen tasks in `playground/` and `sell/app/playground/` (see
      the 2026-08-21 entry above). Cost model for realtime audio still
      unchecked against live pricing — deliberately deferred to the hosting
      decision, not to this build — and it still appears publicly only as one
      **planned, not built** option in the reservation form; the copy in
      `SYSTEM.md` §1 has not been re-read against what actually shipped.
- [ ] Python/FastAPI backend: after the first payment, not before.
- [ ] **LLM grading (designed 2026-08-15, parked — frontend first).** The rubric
      only detects vocabulary, not knowledge: measured 6/6 on nonsense with the
      right words, 6/6 on a *fully reversed* read path, and 4/6 on "I don't
      remember, let me check my notes". The three probe textareas are not wired
      to anything at all — no `value`, no `onChange` — so what you type there is
      never read.

      Agreed shape when it resumes: a Gemini key in a server route
      (`app/api/grade/route.ts`, never the browser), one call grading the recall
      answer plus all three probes together, ground truth taken from the steps,
      rubric labels and chapter answers already in `lib/rep.ts`, output pinned by
      `responseSchema` to `{keys[], verdict, probes[]}`.

      Non-negotiable: **the regex rubric stays as the fallback.** Free tier is
      250–1,500 requests/day depending on the source, so one good post exhausts
      it; on 429, error or >8s the page grades locally and says so, and a daily
      counter degrades before the cap rather than after. A buyer must never meet
      a broken grader at the moment they decide to pay.

      Open question left unanswered: Next route handler (zero new infra) vs
      FastAPI on Railway (matches the stated Python stack, but is the backend
      deferred until first payment). Recommendation on record: route handler
      now, port the prompt and schema unchanged when a real backend exists.

## 2026-08-20 — fourth book theme: phosphor

**What:** `phosphor`, a Pip-Boy CRT theme for the book — near-black green-tinted
glass, aqua-green phosphor text, yellow-green as the reserved colour. Fourth
step in the existing theme cycle (`src/style.css`, `src/app.js`,
`src/template.html`), glyph `◒`.

**Why it is only a token block:** the theme system is one `[data-theme]` block of
CSS variables plus three list entries — nothing else in the book branches on
theme, so a new world costs 22 declarations and no new code. Palette ported from
`~/Desktop/projects/rio-memory/frontend/index.html`, the terminal coach's
Fallout-style CRT.

**The CRT treatment came with it, after a first pass without it.** The tube is
the theme — dropped as a paint cost on 280k words, put back on sight, because
the flat palette reads as "green page", not as a screen. Three parts: a 1px
glow keyed off `currentColor`, so every colour glows in its own wavelength
instead of everything haloing green; a fixed vignette for curved glass; fixed
scanlines at 2-on-1-off under `mix-blend-mode: multiply` with a .14s flicker.
Both overlays are `position: fixed`, `pointer-events: none`, at z-index 400/401
— above the topbar (40), the sidebar (50) and the fullscreen diagram (300), and
they never catch a click. The flicker is off under `prefers-reduced-motion`: a
7Hz strobe over a reading surface is exactly what a photosensitive reader must
not be handed.

**Contrast checked, not eyeballed:** body 14.1:1, secondary 8.8:1, muted 5.3:1,
`--line-strong` 3.6:1 (clears the 3:1 WCAG 1.4.11 asks of control boundaries),
dark ink on the accent 15.6:1.

**Verified in-browser:** cycle reaches `phosphor` in two clicks from paper, the
button reads `◒ phosphor`, body computes to `rgb(8,20,13)` on `rgb(39,255,134)`,
and the chapter diagrams inherit the palette including the highlighted node.

## 2026-08-20 — phosphor on the sell page too

**What:** the same fourth theme on the presale page — token block in
`app/globals.css`, fourth entry in `THEMES`/`THEME_GLYPH`/`THEME_NAME`
(`lib/prefs.ts`), and the CRT treatment scoped to `:root[data-theme="phosphor"]`.
The pre-paint script needed no edit: it validates against `THEMES`, so a fourth
value was already legal, including the `hldgym_v1` hand-off that carries a
reader's book theme onto this page.

**Why the palette moved slightly:** the sell page has a `--panel-2` surface the
book does not. `--ink-3` at `#219b54` reads 4.33:1 there — the same AA failure
the existing comment records for `#6b6b6b` — so it went to `#23a85b` (5.03:1),
and `--line-strong` to `#308753` (3.47:1, clearing the 3:1 for control borders).
Both were pushed back into `src/style.css` so the two products keep one palette.

**Also touched:** `color-scheme: dark` and the `.bookBtn` colour override, both
of which list themes explicitly — a new dark theme has to join both lists or the
scrollbars come back white and the free-book button loses its label.

**Verified in the built site, not the dev server:** `npm run publish:book`, then
served `dist/` and cycled to phosphor — body paints `rgb(8,20,13)`, the overlay
computes `mix-blend-mode: multiply` at z-index 201, and `elementFromPoint` over
the rep's *watch* button returns the button, so the two fixed overlays do not
eat clicks. Reels keep the dark cut, as they do under manim. `tsc --noEmit` and
`eslint` both clean.

**Symptom worth recognising:** a plain `python3 -m http.server` sends no cache
headers, and Chrome served the previous `index.html` after a rebuild — the CSS
was in `dist/` while the page still computed the old rules. A query string or a
hard reload settles it; the fix is never in the stylesheet.

---

## 2026-08-21 — the playground: a fourth pipeline, dictation, a live interviewer, a coach handoff, and the session cap

**One entry for thirteen tasks, not thirteen entries.** `sell/AGENTS.md` calls
for an entry per unit of work, not per commit, and the unit here is the whole
playground feature: a self-hosted Python voice service (`playground/`, the
fourth pipeline, writing nothing into `../dist/`) plus its browser page
(`sell/app/playground/`) and a mic control folded into the existing rep
(`sell/components/Rep.tsx`). Spec at
`docs/superpowers/specs/2026-08-21-playground-design.md`.

**What shipped.** Two modes on one FastAPI service holding the OpenAI key,
talked to over a self-hosted WebRTC connection (`SmallWebRTCTransport`, no
vendor lock-in): **dictation** (mic → VAD → STT → data channel, no LLM, no
TTS, nothing talks back — it fills the existing recall textarea hands-free)
and **playground** (the same pipeline with an LLM and TTS stage added, a
live voice interviewer that pushes back on one rep, p1c06, then hands off to
a coach who has the answer key). Cascaded STT/LLM/TTS throughout, deliberately
not speech-to-speech — every stage is a normal OpenAI model call the rest of
the stack can reason about and test. Silero VAD and SmartTurn both run
locally, no round trip for turn detection. The board (Excalidraw) is read as
a diffable graph, not a screenshot — nodes and edges in, a one-line "since the
last update: added Cache, connected App to Cache" summary out — because a
coach that can name what just changed is the whole reason to build this
rather than a plain voice memo. The interviewer never sees the rubric or the
follow-up answers; only the coach does, and only from the moment it takes
over. `playground/rep.py` is a hand-ported second copy of `sell/lib/rep.ts`
(Python cannot import TypeScript), and `test_personas.py`'s
`TestNoDriftFromTheFrontend` fails the moment the two disagree — REP_TITLE
included as of the fix-wave entry below. That guard only runs when someone
runs the Python suite by hand, though: there is no CI, and nothing in
`sell`'s own `npm run build` touches `playground/` at all, so "fails" means
"fails whenever this is next run," not "fails the build."

**This task's own piece: the session cap.** Voice bills by the minute, so a
session has to end whether or not anyone remembers to stop it — and it has to
end in a way that never leaves the learner cut off mid-round with no
explanation, which is worse than not building the cap at all. `Session` grew
three methods, all taking `now: float` rather than reading the wall clock
themselves, so the tests stay deterministic: `start(now)` marks the clock,
`remaining_secs(now)` is `config.session_cap_secs` before `start()` and never
goes negative after, `expired(now)` is `remaining_secs(now) <= 0`
(`playground/tests/test_cap.py`, 5 tests). `server.py` calls `start()` the
moment a playground worker is built, and a background task
(`_enforce_cap`) polls the same clock: at 80% of the cap the interviewer
becomes the coach — persona switched, context refreshed with the answer key,
TTS re-voiced, and (unlike the interviewer's own `end_round` tool call, which
has a function-result callback to trigger the next completion for free) an
explicit `LLMRunFrame()` queued to the worker, because nothing else would ask
the model to actually speak the handoff. At 100% the connection is cut —
through `_end_session`, the exact same idempotent teardown the "closed" and
"failed" connection handlers already use for an ordinary disconnect, not a
second way to tear a session down. The cap is announced in the page copy
before a session ever starts (`sell/app/playground/page.tsx`: "Sessions run
up to 12 minutes. The interviewer hands over to the coach before time is up,
so you always get the walkthrough."), never sprung at the moment it bites.

**A real bug the cap's own test setup caught.** `_enforce_cap` originally
polled on a flat 1-second sleep. At the 12-minute default the 80%-mark
handover window is 144 seconds wide, so a 1-second granularity never mattered
and every hand-check looked fine. Set the cap to a few seconds instead — which
the task brief asks for specifically so nobody waits twelve minutes to find
out — and the handover window shrinks to under a second, smaller than the
poll interval, and the loop can step clean over it: straight from "not handed
over yet" to "expired," the interviewer cut off with no coach at all, exactly
the outcome the cap exists to prevent. Reproduced with a standalone script
against the real `_enforce_cap` (fakes only for the worker/runner/connection)
at `session_cap_secs=4`: it hung forever, because a second bug compounded the
first — the verification script's own `await watcher` on "has the mode
become coach yet" never returned once the handover never fired. Fixed by
capping each sleep at the time left until the handover instant itself, not
just at a flat ceiling, so the loop can never sleep past it. Re-run at
`session_cap_secs=4` and `session_cap_secs=2`: handover lands within 0.02s of
the 80% mark, the cut lands within 0.01s of 100%, every time.

**A second real bug in the same function, found on review, not by this
build's own live runs.** `_enforce_cap`'s handover branch gated only on its
own local `handed_over` flag, never on the session's actual mode — but a
round can reach coach mode *before* the cap fires, through the interviewer's
own `end_round` tool call, which runs independently of the cap, and nothing
ends the connection when it does. A live session already in coach mode when
the 80% mark arrives is therefore routine, not exotic. The branch would
re-run `switch_to_coach()`/`push_context()` (harmless — both are
idempotent) but also force-queue a *second, unprompted* `LLMRunFrame` with
no user turn behind it: the coach interjecting out of nowhere
mid-conversation. **Symptom if it breaks again: the coach cuts in on its own
during a normal exchange, for no reason the transcript explains.** None of
this task's own live runs could hit it — every one used a short cap
specifically to exercise the cap itself, so `end_round` never got the chance
to fire first. Fixed by gating the whole block (not just `handed_over`) on
`pg_session.mode != "coach"`.

**`_enforce_cap` had zero regression coverage until this same review pass.**
`test_cap.py` only covers the pure `Session` methods; the scheduling and
polling logic — where the flat-interval bug above was found and fixed — had
been verified once, live, and with a throwaway script, and then left with no
test at either level. `Session`'s injected clock and the worker/connection
being trivially fakeable (exactly what the throwaway script already did)
made this the same call as `_allowed_origins()` below, just with more at
stake: committed as `TestEnforceCap` in `test_server.py` (3 tests, real
timing, ~2.5s total) — handover before the cut, a `session_cap_secs=0.5`
cap still getting a handover rather than a bare cut (the flat-poll bug's
exact regression case), and a session already in coach mode getting no
second run frame (this bug's regression case). Mutation-tested the second
one directly: reverting the `pg_session.mode` gate back to `handed_over`
alone fails `test_a_session_already_in_coach_mode_gets_no_second_run_frame`
with an extra queued `LLMRunFrame` in the diff — confirmed, then reverted.

**Bugs, recorded by symptom** — the symptom is what a future session
recognises, not the diff that fixed it:

- Pipecat 1.7.0 moved VAD out of `TransportParams` into a pipeline processor
  (`VADProcessor`) and turn detection into `UserTurnStrategies`;
  `PipelineTask` and `PipelineRunner` are both deprecated in favour of
  `PipelineWorker`/`WorkerRunner`. Anyone following an older tutorial writes
  code that imports fine and does not run.
- Server messages must be wrapped in the RTVI envelope
  (`{"label": "rtvi-ai", "type": "server-message", "data": ...}`) or
  `@pipecat-ai/small-webrtc-transport` parses the data-channel message off the
  wire and silently drops it before it reaches `onServerMessage`. **Symptom:
  you speak, and nothing appears — dictation looks dead.** This shipped
  undetected through two task reviews because every test in this build ran
  with the service down; nothing exercised the wire format until a live
  connection did.
- `LLMContext.set_messages()` replaces *all* messages, not just the system
  ones. **Symptom: the interviewer forgets the conversation, and the coach
  arrives knowing nothing about what was drawn or said** — `Session.push_context`
  exists specifically to filter-and-splice instead of replacing wholesale.
- A `VADProcessor` in the pipeline plus a second VAD handed to the user
  context aggregator (`LLMUserAggregatorParams(vad_analyzer=...)`) builds two
  Silero instances analysing the same audio, and the upstream STT service
  transcribes on every stop frame it sees from either one. **Symptom:
  duplicated transcript lines, and an OpenAI bill roughly double what the
  session should cost.**
- Coach-drawn elements carry `customData.author === "coach"`, and the board
  reader excludes them from what gets read back into context. **Symptom if it
  breaks: the coach praises components the learner never drew.**
- The interviewer's context holds no answer key, enforced by
  `test_personas.py`. **Symptom if it breaks: the interviewer starts
  helping.**
- `playground/rep.py` duplicates `sell/lib/rep.ts` because Python cannot
  import TypeScript; `test_personas.py` parses the `.ts` source and fails the
  moment the two disagree.

**Two more, found during this task's own verification, not on the original
list.** Both are the direct result of actually running the pieces together
instead of reasoning through them, which is the entire point of this task:

- The FastAPI service shipped with no CORS policy at all. `sell` and
  `playground` are different origins by design — `:3000` and `:7860` in dev,
  and a different deployment target in production per
  `NEXT_PUBLIC_VOICE_URL` — so every browser fetch to `/api/offer` failed
  preflight before an SDP offer or a mic prompt ever happened. **Symptom: a
  live, correctly-running service is unreachable from the browser,
  indistinguishable from the service being down at all.** No earlier task
  report caught this because none of them had an OpenAI key to bring the
  service up with in the first place — this task used a
  syntactically-present-but-invalid key (`sk-broken`) specifically to get far
  enough to find out. First fixed with `CORSMiddleware(allow_origins=["*"])`;
  **narrowed on review** — see below, that first pass was broader than it
  needed to be.
- The polling bug described above. **Symptom: with a short-enough cap, the
  session reaches the cut having never handed over at all** — invisible at
  the 12-minute default, guaranteed at a test-sized one.

**Three more, found the same way and fixed on the same review pass, all
variations of one defect: the page claiming voice is working when it is
not.** This repo's first standing rule is never to claim the product does
something it does not, and the spec's failure-mode section is explicit that a
denied microphone must drop to text mode and say so out loud — none of the
three did, and all three are now fixed and re-verified live:

- **Mic denied showed "listening."** `@pipecat-ai/client-js` swallows a
  `getUserMedia` rejection internally (logged only as a console warning,
  "Devices Error (Permission Denied)") and lets `connect()` resolve anyway,
  with no live audio track. **Symptom: the learner speaks, believes it is
  working, and gets nothing** — the worst of the three, because nothing about
  it looks broken. Fixed in `lib/voice.ts`: after `connect()` resolves,
  `client.mediaState.mic.state` (the SDK's own purpose-built per-device
  status — `connect()` already awaits `initDevices()` to completion first, so
  it has settled to `"granted"` or an error by the time `connect()` returns)
  is checked explicitly rather than assumed from a successful connect. Not
  `"granted"` → disconnect and throw, which every existing caller already
  catches and falls back to the keyboard for, so `Rep.tsx` and `page.tsx`
  needed no new branch for this case, only the new check itself.
- **A server-initiated teardown never reached the page.** State stuck at
  `"live"`/`"on"` after the *server* ended the session (the cap, most
  reachably) — a live-looking session that was already dead. Fixed by wiring
  `PipecatClient`'s own `onDisconnected` callback (already part of the SDK,
  never listened to before this) in `connectVoice()` to a new
  `onDisconnect()` option, called by `Rep.tsx`/`page.tsx` to drop back to
  `"unavailable"`/`"unreachable"` — the same honest state a failed connect
  already shows. Guarded by a `live` flag so a disconnect the *caller* asked
  for (the mic toggle's own click-to-stop) never fires it — verified live
  (below) that a deliberate stop still returns cleanly to "off", not
  "unavailable".
- **A fatal server-side error never reached the page.** Investigating this
  corrected something stated flatly, and wrongly, earlier in this same entry:
  pipecat's own `RTVIProcessor` already relays *every* `ErrorFrame` to the
  client as a native RTVI `error` message (`processor.py`: `elif
  isinstance(frame, ErrorFrame): await self._send_error_frame(frame)`) — the
  401 in the verification below really was reaching the browser the whole
  time. The actual gap was one layer up: `PipecatClient` exposes this as an
  `onError` callback, and nothing in `voice.ts` was listening for it, so the
  app dropped it silently. **Symptom: a fatal error resolves into a
  perfectly quiet, still-`"live"`-looking page — not a hang, worse, an
  active-looking session doing nothing.** Fixed the same way as the teardown
  above and through the same path, per the review's own instruction not to
  build a second mechanism: `onError` now calls `client.disconnect()` itself
  (this app has no retry UX and no error taxonomy — any relayed service error
  is treated as fatal to the session, full stop) and the resulting
  `onDisconnected` does the actual notifying. No server-side change was
  needed for this one at all.

**CORS narrowed, on review.** `allow_origins=["*"]` was right that the
service holds no cookie or session to leak, but wrong about the actual risk:
a wildcard means *any* page open in the same browser while this service is
running locally — not just `sell`'s — can open a session against it and
spend the visitor's own OpenAI quota. `server.py` now reads
`PLAYGROUND_ALLOWED_ORIGINS`, a comma-separated list, same env-var convention
`VoiceConfig.from_env()` already uses, defaulting to the two localhost
origins `sell` actually runs from (`http://localhost:3000`,
`http://127.0.0.1:3000`) — a standalone `_allowed_origins()` function rather
than a new `VoiceConfig` field, since CORS is an app-wide policy fixed at
startup, not a per-session tuning knob re-read on every `/api/offer`. Three
tests in `test_server.py` cover the default, an override replacing it
entirely, and comma/whitespace handling. Verified directly with `curl`:
`Origin: http://localhost:3000` gets `access-control-allow-origin:
http://localhost:3000` back; `Origin: https://evil.example` gets no
CORS header at all, which is what makes the browser refuse the response.

**`PLAYGROUND_ALLOWED_ORIGINS="*"` undid the whole fix, found on the same
review.** Garbage, whitespace, and trailing commas all degrade safely to a
smaller list — but `"*"`, the standard "allow everything" convention and the
first thing anyone reaching for a wildcard would type, was accepted verbatim
and handed straight to `CORSMiddleware`, which treats it as allow-all.
**Symptom if it breaks again: the origin allowlist exists in the code and in
this entry, and is silently worth nothing.** `_allowed_origins()` now raises
`ValueError` if `"*"` appears anywhere in the parsed list (bare, or mixed
with real origins) — failing loudly at import time, before any session
exists, which is free and is the honest behaviour for a security setting.
Two new tests cover both cases; also confirmed directly, setting
`PLAYGROUND_ALLOWED_ORIGINS=*` and importing `playground.server`, that the
module now refuses to load at all, with a message naming the actual risk,
instead of starting up wide open.

**Verified by causing each of the four failure modes, not by reasoning about
them:**

1. **Service down.** `npm run dev` alone, playground not running: typed a
   full answer into the recall textarea, submitted, `recall · 6 of 6` —
   grading is unaffected. `/playground/` shows "voice service unreachable"
   with no crash and no hung spinner. Run twice, once before and once after
   this task's other changes, on a fresh browser context both times. This is
   the property that has held through every task in this build and had to
   keep holding after this one; it does.
2. **Mic denied.** Simulated by rejecting `getUserMedia` from an injected
   init script (headless Chromium auto-grants a fake device otherwise, so a
   real deny dialog was not available to test against). With the service
   fully down, the control correctly settles on "voice is unavailable, type
   it instead" and typing still works, as before. With the service actually
   reachable (`OPENAI_API_KEY=sk-broken`) — the case that used to show
   `◉ listening` for a session hearing nothing — the control now correctly
   settles on the same "voice is unavailable... type it instead" state, still
   enabled, still retryable; typed a full answer and submitted, `recall · 5
   of 6` (a deliberately slightly-off answer), grading unaffected. Also
   checked the case this fix must not break: with the mic genuinely granted
   (no injected rejection), the control reaches real `◉ listening`, and a
   *deliberate* second click — the toggle's own stop — returns cleanly to
   `◎ speak it` with the ordinary "or type it" copy, not "unavailable"; the
   `live`-flag guard in `connectVoice()` is what keeps a caller-requested
   disconnect from being mistaken for an involuntary one.
3. **Bad key.** No real OpenAI key exists anywhere in this build, so this one
   still could not be tested the way the other three were — but
   `OPENAI_API_KEY=sk-broken` again got further than expected, and further
   than the first pass through this task found. The service starts, `/health`
   reports `key_loaded: true` regardless of validity, and `/api/offer`
   succeeds — the OpenAI client library only validates a key against the
   network, at the moment of a real call, not at construction. Confirmed live
   end to end, and re-verified after the fix: the interviewer's first real
   completion attempt returned an actual `401 - Incorrect API key provided`.
   The brief's stated behaviour — **"the client reports it plainly"** — now
   holds, but the earlier claim in this same entry that nothing relays the
   error was wrong and is corrected above: pipecat's `RTVIProcessor` was
   already forwarding it as a native RTVI `error` message the whole time; the
   app just wasn't listening. With `onError` now wired, the browser closes
   the connection itself within milliseconds of the 401 (log timestamps: peer
   connection established 21:18:40.854, the 401 logged at 21:18:48.191, the
   connection already `closed` at 21:18:48.213 — about 7.36s after connect,
   under the 8s cap this run used, so the client's own reaction beat the
   cap's to it) and the page settles on "voice service unreachable." Whether
   a *genuinely* invalid key (well-formed, rejected only on scope/billing)
   relays the same way is unverified — no such key was available, though the
   mechanism (any `ErrorFrame`, regardless of cause) does not depend on which
   kind of failure produced it.
4. **Session cap.** Verified twice on the first pass (live end to end and
   against fakes — see above and below), then re-verified live a third time
   after items 2-3's fixes landed, using the same real browser + real
   `uvicorn` + `PLAYGROUND_SESSION_CAP_SECS=8` + `OPENAI_API_KEY=sk-broken`
   setup: handover and the answer key reaching the coach's context, same as
   before; this time the browser's own `state` also correctly left `"live"`
   and settled on "voice service unreachable" (confirmed ~13s after clicking
   "start the round," well past the 8s cap) instead of sticking on `"live"`
   forever, which is what it did before `page.tsx` was wired to
   `onDisconnect`. In this run the *error* relay closed the connection first
   (see item 3), so this exercised the same client-side `onDisconnected`
   handler the cap's own cut would use if a session ran long enough to be cut
   with no error ahead of it — a scenario this build's lack of a real OpenAI
   key cannot produce, since the coach's forced handoff always attempts a
   real completion and always fails the same way with `sk-broken`.

**Never run against the live API, stated plainly, because no OpenAI key was
available at any point in this build:** VAD tuning by ear, the audible
handover (the coach's voice actually changing mid-sentence, not just the
`set_voice()` call being made), the interviewer's refusal to help under
pressure, the coach's drawing arriving end to end, the three model names
(`gpt-4o-transcribe`, `gpt-5`, `gpt-4o-mini-tts` — a real 401 confirms
authentication is checked before the model name, not that the names
themselves are correct), and the real cost per minute. This repo's first
standing rule is never to claim the product does something it does not; none
of the above is claimed to work, only to be wired up correctly by inspection
and, where a broken key could reach it, by a live but auth-failing call.

**No automated test for the `lib/voice.ts` changes, and that is a real gap,
not an oversight.** `_allowed_origins()` got three cheap tests because it is a
pure function of an env mapping. `connectVoice()`'s new logic — the
`mediaState.mic` check, the `live`-flagged `onDisconnected`/`onError`
wiring — is not: it is a thin wrapper around `@pipecat-ai/client-js`'s own
`PipecatClient`, constructed directly inside the function, and `sell` has no
mocking infrastructure (`npm test` is plain `node:test` against `lib/*.ts`,
nothing component- or SDK-level is mocked anywhere in this repo — `Rep.tsx`
and `voice.ts` have never had unit tests, verified live in every task that
touched them instead, same as this one). Checked whether that's actually
true or just assumed: `connectVoice` doesn't take an injectable client
factory, and adding one only to make a test possible would be a
purpose-built seam that exists for no reason but the test, not a reflection
of anything the function itself needs — the honest move as recorded, verified
live above, three separate ways with a real browser and a real service.

**All 95 Python tests pass** (`playground/.venv/bin/python -m unittest
discover -s playground/tests -t .` from the repo root — 82 before this task,
5 in `test_cap.py`, 3 in `test_server.py` for `_allowed_origins`, 2 more
there for the `"*"` rejection, 3 more for `TestEnforceCap`), **all 36 `sell`
tests pass**, lint is clean, and `npm run build` still produces the static
export including `/playground`.

---

**Fix wave, from a whole-branch review of the thirteen tasks above.** One
pass, applied together rather than as separate entries, because every finding
traces back to the same feature. Two were load-bearing enough to block a
publish; the rest are correctness and honesty cleanups the review also found.

**The unfinished Playground would have gone live on the next publish.**
`next build` happily emits `out/playground/index.html` — it is a route like
any other — and `publish:book`'s rsync had no exclude for it, so the next
`npm run publish:book` would have put a public `/playground/` on the sales
page with `NEXT_PUBLIC_VOICE_URL` unset in production, meaning the page
would announce a session and then never be able to connect. The spec is
explicit that nothing goes on the sales page until §9 and *What you are not
buying* are re-read line by line, and that re-read has not happened.
Fixed with a third `--exclude 'playground/'` in `publish:book` — verified by
building `sell` and dry-running the exact rsync command both with and
without the new exclude: without it, `dist/playground/` gains six files
(`index.html` among them); with it, the dry-run plan contains zero mentions
of `playground` and `git status` shows no change under `dist/` at all. Root
`AGENTS.md` reworded the line that hid this: "`playground/` writes nothing
into `dist/`" was true of the Python service and misleading as written,
since the client half (`sell/app/playground/`) is part of `sell`'s own build
and would ship without the exclude — `sell/AGENTS.md`'s hard rules gained the
matching bullet.

**The interviewer could call `draw_diagram`.** `context.set_tools()` was
called once, at pipeline-build time, with both `END_ROUND` and
`DRAW_DIAGRAM` in the list, and nothing ever narrowed it afterward — the
same class of bug as the interviewer holding the answer key: an interviewer
that can draw can show the candidate the structure the round exists to
measure. Moved the decision into `Session`, the one place mode already
lives: `Session.tools()` returns `end_round`-only in interview mode and
`draw_diagram`-only in coach mode, and `push_context()` — already the one
place that writes mode-driven state into the live `LLMContext` — now calls
`context.set_tools(self.tools())` alongside its existing message refresh.
Both existing callers that flip the mode (the `end_round` handler in
`pipelines.py`, the cap's handover branch in `server.py`) get the narrowed
list for free, with no code change at either call site. Ten new tests cover
both orderings (a context bound while still in interview mode, and one
already bound before a live switch to coach) and both real call sites
(`_end_round` and the cap's `_enforce_cap`), against both the real
`LLMContext`/`ToolsSchema` (via a real `build_playground_worker`) and the
suite's fakes. Mutated `Session.tools()` to always return both tools: 8
tests failed across `test_session.py`, `test_pipelines.py`, and
`test_server.py`. Reverted.

**The Playground page conflated a finished round with a dead service.**
Every terminal state — a session that ran its course and handed over to the
coach before the cap cut it, a fatal service error, and a denied
microphone — rendered the same "voice service unreachable." The spec
requires a denied mic to say so out loud, and this repo's first standing
rule is never to claim the product does something it does not; reporting a
*working* round's normal end as a dead service is exactly that claim, just
in the other direction. `sell/lib/voice.ts`'s `onDisconnect` now carries a
reason (`"error"` only when RTVI's own `onError` fired first; `"ended"`
otherwise), and `page.tsx` catches `connectVoice`'s specific
`Error("microphone unavailable")` separately from any other connect
failure. Four states now render distinct, honest copy: `idle`/`connecting`,
`denied`, `unavailable`, and `ended` — matching the honesty `Rep.tsx`'s own
mic control already had, extended with the one distinction dictation never
needed: telling a completed round apart from a broken one.

**The "12 minutes" copy was already wrong once, live, in this same build's
own verification** (task 13's run used an 8-second cap under a page that
said twelve minutes). The cap is `PLAYGROUND_SESSION_CAP_SECS`,
env-configurable, and `sell` is a static export with no way to read that
value at build time. Chose the smaller correct fix: reworded the copy to a
claim that holds regardless of the configured cap ("Sessions run for a
capped length...") rather than fetching the real number from `/health` at
runtime. `/health` returning the cap was the other option on the table, and
would have been more precise, but it adds a runtime dependency (a fetch on
mount, a loading state, a fallback for when it fails — which in production,
with `NEXT_PUBLIC_VOICE_URL` unset, is *every* time) to solve a problem that
doesn't need the exact number, only a copy that's true. `/health`'s own
gap — it exists, reports `key_loaded`, and has no caller anywhere — stands as
recorded, not closed by this pass.

**The cap task was created before its session was registered.** `offer()`
built `cap_task = asyncio.create_task(_enforce_cap(...))` and only assigned
`_sessions[pc_id]` afterward — correct today only because nothing awaits
between the two lines, so the scheduled task can't take its first step
before the assignment lands. Add an `await` later (an easy, invisible
change) and `_enforce_cap`'s own `while connection.pc_id in _sessions` reads
false on entry, and the cap silently never runs. `offer()` now writes
`_sessions[pc_id]` first, with `cap_task=None`, then creates the cap task
and fills it in with `_Session._replace()`. Covered by
`TestCapTaskRegistrationOrder`, which drives the real `offer()` (fakes for
the connection, `build_playground_worker`, and `WorkerRunner`) and checks
`_sessions` state from inside a mocked `_enforce_cap`'s own call, not by
timing — timing is exactly what let the old order look correct. Mutated
`offer()` back to the old order plus an explicit `await asyncio.sleep(0)`
between the two lines (simulating the regression the comment describes):
the new test failed. Reverted.

**`sell/lib/rep.ts` had no pointer to its second copy, and the drift guard
didn't cover `REP_TITLE`.** `playground/rep.py` is a hand-port because
Python cannot import TypeScript, and `test_personas.py`'s
`TestNoDriftFromTheFrontend` is what stops the two disagreeing silently —
but nothing in `rep.ts` said so, and the guard itself only ever compared
`RUBRIC`'s labels and `PROBES`, never `REP_TITLE`, which is the one value
the interviewer prompt actually interpolates. Added a comment at the top of
`rep.ts` pointing at `playground/rep.py` and the drift test, and a fourth
test, `test_rep_title_matches_rep_ts`, alongside the other two. Also
corrected this same entry, above: it previously said the drift test "fails
the build the day the two disagree" — there is no build that runs the
Python suite, no CI, and `sell`'s own `npm run build` never touches
`playground/`, so that was never true and has been reworded to what is.

**Verification for this pass:** full suites both sides — 105 Python tests
(95 before, +10: 3 in `test_pipelines.py`, 4 in `test_session.py`, 2 in
`test_server.py`, 1 in `test_personas.py`), 36 `sell` tests (unchanged, none
of this pass's `.tsx`/`.ts` changes have dedicated unit coverage — the same
documented gap noted above for `voice.ts`, now also true of `page.tsx`'s new
state logic, exercised by `tsc --noEmit` and `eslint` passing clean but not
by a test that could fail on its own) — `npm run lint` and `tsc --noEmit`
both clean, `npm run build` still ends `○ (Static)` and still emits
`/playground`, and the rsync dry-run above confirms it stays out of
`dist/`.

## 2026-08-22 — Playground gets a Google sign-in, because someone else's rule fired

**What shipped.** `POST /api/offer` now gates `mode=playground` on our own
session token, sent as `Authorization: Bearer <token>` — never a query
string, which leaks into every server log line it passes through. No valid
token, no session: the check runs before `SmallWebRTCConnection()` is even
constructed, so a rejected request bills nothing. `mode=dictation` is
untouched and needs no token at all — a deliberate asymmetry, not an
oversight, because dictation has no LLM or TTS stage and costs nothing per
minute the way playground does.

The browser shows Google Identity Services' own "Sign in with Google"
button (`sell/lib/auth.ts`) when no locally-valid token is on hand. Its ID
token goes to a new `POST /api/login`, which verifies it with `google-auth`
(`google.oauth2.id_token.verify_oauth2_token` — signature, issuer,
audience, expiry) and, only on success, mints our **own** token: not a JWT.
`base64url(payload_json) + "." + base64url(hmac_sha256(secret,
payload_json))`, verified with `hmac.compare_digest`, never `==`. No `alg`
field means there is nothing for an algorithm-confusion attack to parse.
Google's token expires in about an hour; ours lasts
`PLAYGROUND_SESSION_TTL_SECS` (7 days by default), so a returning learner
isn't re-prompted every session. `sell/lib/voice.ts` moved off the
deprecated `connectionUrl` to `webrtcRequestParams` to carry the header —
the only shape of the two that has one.

**Why: not the trigger `SYSTEM.md` §9 had on record.** That table's Auth row
predicted auth would arrive *when reps are per-user* — a login gating
content. That never fired, and still hasn't: the sell page still has no
login anywhere between a visitor and the reservation form. What actually
fired is a different problem the table never named: Playground is a
metered service that spends real OpenAI credit per minute of audio, sitting
behind an endpoint any browser on the internet could reach directly and
start billing against, with no visitor and no payment link anywhere near
it. `SYSTEM.md` §9 now records the real reason rather than the old
prediction pretending to have come true.

**There is no allowlist.** Anyone with a Google account is let in — a
decision made knowingly, after the trade-off was shown, not an oversight
left for later. The two things actually standing between this endpoint and
an open bill are unrelated to who signs in: the service binds to
`127.0.0.1` by default (no `--host` flag in `playground/README.md`'s run
command — it is not reachable from outside the machine it runs on at all
today), and the per-session wall-clock cap
(`PLAYGROUND_SESSION_CAP_SECS`) bounds what any one session, forged or not,
can spend. **Hosting Playground anywhere removes both** — a public host is
reachable by definition, and a determined abuser can still open many capped
sessions back to back. That is the condition under which "no allowlist"
needs revisiting, not a hypothetical: the day this leaves `127.0.0.1`, an
allowlist or a per-account rate limit stops being optional.

**How it was proven, not just written.** TDD throughout: `playground/auth.py`
and its 17 tests in `playground/tests/test_auth.py` existed before the
implementation did — sign/verify round trip, expiry, a tampered payload, a
tampered signature, a wrong secret, malformed/junk/empty tokens,
`token_secret_from_env`'s missing-secret refusal, and the Google wrapper's
failure handling against a stubbed verifier (never a real network call).
Five mutations were run against the working tree and reverted: an expired
token accepted (caught), the signature check skipped (caught, 4 tests),
`compare_digest` swapped for `==` (caught — see the security-review
correction below), the service starting with no secret (caught), and
dictation gated by mistake (caught, 4 tests — 2 of them incidentally, in
`TestConnectionLeakGuard`, which had never needed to pass an
`authorization` argument before). 138 Python tests total (105 existing +
33 new), 36 `sell` tests unchanged, both `npm run lint` and `tsc --noEmit`
clean, `npm run build` still ends `○ (Static)`. `VoiceConfig` gained its
first `int` field (`session_ttl_secs`) and `from_env()` gained int coercion
alongside the float coercion it already had — a gap the brief flagged
rather than one found the hard way.

**Security review, same day: one Critical, one wrong claim in this very
entry, five cheap minors.** The Critical: `offer()`'s renegotiate branch (a
repeat `POST /api/offer` carrying an existing `pc_id`) gated on *that
request's own claimed* `mode` query param, not on what the session being
touched actually was. `?mode=dictation` needs no token — so a caller who
knew a **playground** session's `pc_id` could renegotiate it, unauthenticated,
by simply claiming `mode=dictation`, and take over its live, billing
connection: the attacker's SDP becomes the remote description, and they
hear the interviewer on someone else's cap. `?mode=playground` on the same
`pc_id` correctly 401'd — only the cross-mode route was open. Fixed by
recording each session's real mode on `_Session` itself at creation
(`mode: Mode`, not inferred from `cap_task is not None`, which happened to
be an equally correct discriminator today but ties the auth gate to a
completely different feature — the cost cap — by accident rather than by
name) and gating on `existing.mode`, not the request's `mode` param, when
`request.pc_id` names a session that already exists. `pc_id` is a
`uuid4().hex` an attacker cannot guess, and the service binds `127.0.0.1`
by default, so this was not reachable in today's deployment — but neither
of those is an auth check, and both are exactly the two things this entry
already named as evaporating the day this is hosted. Regression-tested
directly (`TestRenegotiateAuthGateBypass`, `playground/tests/test_server.py`):
proved caught by reverting the fix and watching the new test fail, then
restored.

**The wrong claim, in the paragraph directly above:** this entry originally
said `compare_digest` swapped for `==` was **not caught**, "a known, accepted
gap in what a functional test suite can prove." That is false, and the
security review proved it false by writing the test: patch
`playground.auth.hmac.compare_digest` with a spy, drive the real
`verify_token()`, and assert the spy fired. Unmutated, it fires once;
with `==` substituted, it never fires at all, because `==` is a language
operator the patch cannot intercept — the spy's silence *is* the signal.
That is a functional test exercising the real code path, not a source
grep, and it now lives in `test_auth.py`
(`test_verify_token_actually_calls_compare_digest_not_a_plain_equality`).
The mutation table is 5/5, not 4/5. The lesson worth keeping isn't about
HMAC — it's that "a functional suite structurally cannot observe X" is a
claim to verify by trying, not a conclusion to write down on the strength
of it sounding right.

Five minors, all fixed same pass: `sell/lib/auth.ts` gained tests
(`isTokenLikelyValid` is a parser — base64url decode, `JSON.parse`, an
expiry compare — on the auth path, and had none); `clearToken` (written,
exported, never called) is now wired into the client-side-valid-but-
server-rejected path it existed for; `/api/login` no longer echoes
`google-auth`'s raw exception text (which included the caller's own
submitted credential) into the 401 body — a fixed message goes to the
caller, the detail goes to the server log; `verify_google_id_token`'s
`except Exception` no longer reports a Google outage (a cert-fetch
transport failure) as "bad credential" the same way it reports an actually
bad one; and `playground/.env.example` now lists
`PLAYGROUND_GOOGLE_CLIENT_ID` and `PLAYGROUND_TOKEN_SECRET` as commented
placeholders, so `cp .env.example .env` no longer hands a fresh clone a
service that fails closed with no clue why.

**One thing the review flagged that was not a bug:** it read the
`http://localhost:3000` / Google Cloud Console origin error in the browser
console as a real misconfiguration needing a fix. It is not — Google's own
exported credentials JSON already lists both `http://localhost:3000` and
`http://127.0.0.1:3000` as authorized origins for this client ID, matching
both `.env` files exactly. The browser error was origin-propagation delay,
which Google documents as taking up to several hours after a client ID is
created or edited. No Google config was changed, and no doc note was added
telling a future reader to change it.
