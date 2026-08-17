# System Design

The design system for HLD Gym and the Sprint.

Named without apology: it is the design system for a system design product, and
the joke is the point — the name says the visual language and the subject are
the same discipline. A diagram that lies about a system is a bad diagram; an
interface that lies about a product is a bad interface. Both are failures of the
same kind.

Descended from Teenage Engineering's design language, adapted for reading.
Anything not specified here should be resolved by asking *"what would the honest
version look like?"* rather than by adding decoration.

---

## 1. Principles

**Constraint is the generative engine.** The palette is small, the type registers
are three, the radius is zero. Restriction is what makes the result look
designed rather than assembled. When you want a new colour, you almost always
want an existing one used correctly.

**Engineered honesty.** Nothing pretends to be something it is not. No fake
depth, no shadows implying elevation that does not exist, no skeuomorphic
texture. A hairline is a hairline. If a control does something, it looks like a
control; if it does not, it must not.

**Lowercase is chrome, capitals are prose.** Everything the machine says about
itself is lowercase — labels, tabs, buttons, status strips. Everything a human
wrote for another human keeps normal sentence case. You can tell at a glance
which voice you are reading.

**Orange is the record button.** TE reserves red for record. Here, the accent is
reserved the same way: the primary action, the active state, the one thing that
matters on this screen. An interface where three things are orange has no
primary action.

**Data has a font.** Anything measured — a count, a price, a score, a step
number, a timestamp — is set in mono. Prose is never mono. Chrome is never
serif.

---

## 2. Colour

### Tokens

Every colour is a custom property on `:root`. **No component ever hardcodes a
hex value**, and no colour is defined only inside a media or `[data-theme]`
block (see §7).

| token | role |
|---|---|
| `--paper` | page ground |
| `--panel` | raised surface (a card, a rep body) |
| `--panel-2` | recessed surface (a header strip, a table head) |
| `--ink` | primary text |
| `--ink-2` | secondary text, supporting prose |
| `--ink-3` | tertiary — captions, mono labels, disabled |
| `--line` | decorative hairline, deliberately low contrast |
| `--line-strong` | a border that is the **only** marker of a control |
| `--accent` | the record button — see §2.2 |
| `--accent-ink` | accent used *as text* on paper (contrast-safe) |
| `--accent-soft` | accent-tinted fill |
| `--good` / `--good-soft` | correct, present, passing |
| `--bad` / `--bad-soft` | wrong, missing, failing |
| `--on-accent` | text placed **on** the accent |

### Three themes

| token | Paper `◐` | Blueprint `◑` | Manim `π` |
|---|---|---|---|
| `--paper` | `#ffffff` | `#0d0d0d` | `#0b0b0f` |
| `--panel` | `#f4f4f4` | `#161616` | `#16161e` |
| `--panel-2` | `#eaeaea` | `#1f1f1f` | `#1f1f29` |
| `--ink` | `#0a0a0a` | `#f0eeec` | `#ececec` |
| `--ink-2` | `#4a4a4a` | `#b0aca8` | `#b9bcc4` |
| `--ink-3` | `#6b6b6b` | `#949494` | `#888888` |
| `--line` | `#d6d6d6` | `#2e2e2e` | `#2c2c36` |
| `--line-strong` | `#8a8a8a` | `#666666` | `#66666f` |
| `--accent` | `#ff5c00` | `#ff6a14` | `#58c4dd` |
| `--accent-ink` | `#b83c00` | `#ff9257` | `#9cdceb` |
| `--accent-soft` | `#ffede3` | `#2a1810` | `#123a45` |
| `--good` | `#167a47` | `#4fbe84` | `#83c167` |
| `--bad` | `#c62a1e` | `#f2705f` | `#fc6255` |
| `--on-accent` | `#0a0a0a` | `#0a0a0a` | `#0b0b0f` |

**Manim** is the 3Blue1Brown palette, carried over from the book unchanged. It
is the one theme where the accent is not orange, and that is intentional — it is
a guest palette, adopted whole rather than tinted to match.

### 2.2 The orange rule

Accent is permitted on:

- the primary action on a screen (one only)
- the active tab or current state
- the single most important number
- the `crux` box — the thing you must not miss

Accent is **not** permitted on: decorative rules, every heading, hover states of
non-primary elements, or anything used more than once per viewport for emphasis.

**"One primary action" is per screen, not per page.** In the hero the buy button
is primary, so the free book is a text link there. In the book's own section
there is no buy button, so the book button *is* the primary and takes the accent
fill. Beside the buy button in the rep it drops back to an outline. The rule to
hold is that **two accent fills never share a viewport** — a screen with two is a
screen with none.

### 2.3 Text on accent is near-black, not white

White on `#ff5c00` is **3.1:1** — fails WCAG AA for body text. Near-black on the
same orange is **6.39:1** — passes. Black-on-orange is also TE's own hardware
labelling convention, so the accessible choice and the authentic one agree.

`--on-accent` is near-black in **all three themes**. Do not "fix" this to white.

---

## 3. Type

Three registers, with hard boundaries.

| register | family | used for |
|---|---|---|
| **UI** | Archivo (grotesque) | headings, buttons, labels, all chrome |
| **Reading** | Literata (serif) | authored prose, and anything a learner writes |
| **Data** | IBM Plex Mono | numbers, measurements, eyebrows, captions, code |

**Never cross the registers.** A heading is never serif. Prose is never mono. A
measurement is never grotesque.

### Scale

| element | size | notes |
|---|---|---|
| `h1` | `clamp(30px, 4.6vw, 54px)` | `-.028em`, `text-wrap: balance`, `max-width: 17ch` |
| `h2` | `clamp(20px, 3.6vw, 26px)` | `-.015em` |
| `h3` | `15px` | UI font, 700 |
| body | `17px` / `1.68` | reading register |
| `.lead` | `20px` / `1.5` | `--ink-2` |
| `.key` | `17.5px` UI 700 | one per section, see §5.7 |
| `.eyebrow` | `12.5px` mono 600 | `.1em`, lowercase, `--accent-ink` |
| `.hint`, `.fact` | `11–12px` mono | `--ink-3` |

Tight negative tracking on display sizes, generous positive tracking on small
mono labels. Line length stays near 65–75 characters via `--measure`, which is
**not** the same as the page width — see §4.

Every rule carrying reading text is `font-size: calc(Npx * var(--fs))` so the
text-size control can scale it (§5.9). A bare `px` in prose is a bug: it will be
the one line that refuses to grow.

Mono labels get `font-variant-numeric: tabular-nums` wherever digits align in a
column.

---

## 4. Geometry

**Absolute rules:**

- `border-radius: 0` — everywhere, no exceptions
- `box-shadow: none` — depth is expressed by borders and surface tokens
- borders are `1px` — `1.3–1.6px` only inside SVG diagrams, where the viewBox
  scales them
- no background gradients, no grid textures, no blur

**Surfaces** are distinguished by token, not elevation: `--paper` for the page,
`--panel` for a raised card, `--panel-2` for a recessed strip inside it.

**Layout is done with flex/grid `gap`**, never per-element margins that collapse
or double. Wide content (tables, diagrams, code) scrolls inside its own
`overflow-x: auto` container; the page body never scrolls sideways.

### Two widths, never one

```css
--shell:   1140px;   /* how wide the page may be   */
--measure: 44rem;    /* how wide a line may run    */
```

These are different questions and were once answered with the same number, which
is the single most common way a page ends up feeling narrow and adrift. Prose
needs ~70 characters or the eye loses the return sweep. **Structure has no such
limit**, and constraining it to the reading width wastes a third of a desktop
screen — the rep panel, which is the whole demo, was rendering a 720-unit
drawing into a 736px column while the space it needed sat empty either side.

- **At the measure:** paragraphs, headings, key lines, eyebrows, lists.
- **At the shell:** the rep, the step grid, terms strips, the price box.
- **Its own rule:** `h1` runs wider than the measure (`17ch`), because a
  headline is scanned in one pass, not tracked line to line.

### Desktop is a different layout, not a wider one

Above 1000px the hero splits: the argument on the left at the measure, the terms
and both calls to action on the right, level with the headline. Simply widening
one column leaves the same page with bigger margins. The terms strip **stacks**
in that column rather than staying a row — four cells in a 364px column would
wrap their captions and go ragged.

The step grid pins to `repeat(3, 1fr)` above 900px. Left on `auto-fit`, the
wider shell fits four columns and leaves the six steps as a ragged 4 + 2.

---

## 5. Components

### 5.1 The self-labelling box

The signature pattern. A box does not float unlabelled — it declares what it is
in a strip on its own top rule.

```
┌──────────────────────────────────┐
│ rep 07 · cache-aside read path   │  ← .repTag, mono, lowercase, on accent
├──────────────────────────────────┤
│                                  │
│  content                         │  ← .repBody
│                                  │
└──────────────────────────────────┘
```

The strip is `--panel-2` for a neutral box, `--accent` with `--on-accent` text
for the one that matters. Bottom border of the strip matches its background when
filled, `--line-strong` when neutral.

### 5.2 Buttons

| class | look | use |
|---|---|---|
| `.btn` | accent fill, `--on-accent` text | the one primary action |
| `.btn.ghost` | transparent, `--line-strong` border | everything secondary |
| `.prefBtn` | bordered, transparent, glyph + name | theme and text size (§5.9) |
| `.bookBtn` | outline that fills with accent once on first view | the free book, in its own section |
| `.fab` | accent fill, fixed, phones only | the free book, floating (§5.10) |

Hover on primary is `filter: brightness(1.07)`. Hover on ghost/icon moves the
border to accent and the text to `--accent-ink` — never a fill change, because
a filled ghost button reads as primary.

Disabled is `opacity: .35` with no filter.

### 5.3 The spec grid

Tables are instrument panels, not documents: mono lowercase headers on
`--panel-2`, a `--line-strong` rule under the head, `--line` between rows, no
zebra striping, no vertical rules. Numeric columns use tabular numerals.

### 5.4 The scorecard

A result list where each row is a claim that was either present or absent.
Present rows are quiet; **absent rows are tinted `--bad-soft`** — the misses are
the message, so they get the weight. A verdict sentence closes it on
`--panel-2`.

### 5.5 The model answer

A left rule in accent, a mono lowercase label, then prose. Used wherever the
system shows its own answer next to the learner's. Never shown before the
learner commits.

### 5.6 The terms strip (`.termbar`)

A hairline row of cells, each a large numeral over a mono lowercase caption.
Used for facts that are numbers: price and dates in the hero, the book's totals
further down. It exists because **the numbers are what a skimming reader
actually takes in**, and burying them inside sentences hides the whole offer.

Rules: numerals in the UI face at 20px with `tabular-nums`; captions ≤ 3 words,
so a cell never wraps to a second line and the row stays even; two columns
below 560px. Never more than four cells — a fifth stops being a glance.

### 5.7 The key line (`.key`)

One bolded UI-face sentence directly under a section heading, carrying that
section's whole point. Every section has exactly one.

The page is built so a visitor who reads **only** the kicker, the heading, the
key line and the terms strip still knows what is sold, what it costs, when it
starts, and why the lock exists. Prose below the key line is optional depth,
never the load-bearing path. Writing a section without one means the argument
lives only in paragraphs, where most readers will not go.

### 5.8 The evidence chart (`.chart`)

A slope chart for a study whose point is a **reversal**. Two hairline axes, one
dashed midline, no grid box, no fills. The losing series is `--ink-3`; the
winning one takes the accent, because the accent is the page's one reserved
colour and this is the claim it is reserved for. It draws itself when scrolled
into view, so the crossover is something you watch happen.

Two rules it exists to record:

- **Series names go in a legend under the plot, never hanging off the line
  ends.** Edge labels force a wide viewBox to hold them, and a wide viewBox in a
  phone column renders its type at ~8px — the same failure §6 exists to prevent.
  Keep everything inside the viewBox and one drawing serves both widths.
- **A chart only ships with numbers checked against the source.** A wrong figure
  on a page asking for money is worse than a vague sentence.

Charts pair with the `.split` layout: prose left at the measure, evidence right
in the column the measure leaves empty.

### 5.9 The preference controls (`.prefBtn`)

Two hairline boxes in the header: text size (`aA largest`) then theme
(`π manim`). Both show **glyph plus name**, because a bare glyph in a box is
unreadable as a control — nothing on the button says what it changes. Names
drop below 560px where the header runs out of width; `aria-label` carries the
full name in both states, and each button reports its **current** value, not the
one it will move to.

Text size is three steps — normal, large, largest — driving `--fs` at 1 / 1.13 /
1.28. Three and not a slider: this is a control someone sets once, and a slider
invites fiddling in place of reading.

`--fs` multiplies reading text only. Two deliberate opt-outs:

- **Header chrome.** The size control lives in the header, and a button that
  resizes itself on click walks out from under the cursor. It is also the one
  row with no room to grow on a phone.
- **SVG labels.** They are sized in viewBox units and already scale with the
  drawing; multiplying again would scale them twice and blow the narrow
  diagram's 10.2px budget (§6).

Any new rule carrying reading text takes `font-size: calc(Npx * var(--fs))`. A
bare `px` in prose is a bug — it will be the one line that refuses to grow.

---

### 5.10 The free-book routes

The book is the distribution, so the page carries five routes to it, each pitched
so it never competes with the buy button:

| place | treatment |
|---|---|
| header | `free` chip, static |
| hero | text link under the CTAs, where buy is primary |
| its own section | `.bookBtn` — no buy button here, so this one takes the accent |
| rep, after grading | outline, because the buy button sits beside it |
| footer | plain link |
| phones | `.fab`, accent fill, fixed bottom-right |

**The floater is bounded at both ends.** It waits for the hero to scroll away —
at the top the hero already offers the book twice and a floater over that is
clutter — and it hides whenever the price box is on screen, because two accent
fills in one viewport leave the eye with no primary action (§2.2).

None of these loop. See §8 for what was tried, why it looked cheap, and what
replaced it.

---

## 6. Diagrams

Diagram styling is a closed vocabulary. Never inline styles on SVG elements.

| class | meaning |
|---|---|
| `.dgNode` | a normal actor box |
| `.dgNodeAlt` | the actor the diagram is *about* — accent-tinted |
| `.dgEdge` | any line, lifeline or arrow |
| `.dgArrowhead` | the shared marker fill |
| `.dgTxt` | actor label, 13px mono |
| `.dgTxtS` | step label, 11px mono, `--ink-3` |
| `.dgDraw` | a line that animates itself in |
| `.dgPart` | a node or label that fades in |
| `.dgOn` | applied to a `<g>` to reveal its contents |

### Two widths

Every animated diagram exists twice: **wide** at viewBox width 720 for the
reading column, **narrow** at viewBox width 320 for phones, swapped by CSS at
720px.

The rule that makes this necessary: an 11px label in a 720-unit drawing rendered
into a 297px phone column arrives at **4.5px**. At viewBox 320 the same label
arrives at **10.2px**.

The rule that makes it possible: **draw lengths are computed from endpoint
coordinates, never `getTotalLength()`**, which returns 0 on a hidden element.

Swap selectors must be qualified (`.stage svg.dgWide`) — a bare class loses to
`.stage svg` on specificity and silently renders both diagrams stacked.

---

## 7. Theming and text size

Two preferences live on `<html>` as data attributes, written before first paint
by an inline script so nothing flashes: `data-theme` and `data-fs`. Both match
the book's exactly — the two products should not feel like two products.

**Text size** is one multiplier, `--fs` at 1 / 1.13 / 1.28. Every reading-text
rule is `font-size: calc(Npx * var(--fs))`; a bare `px` in prose is a bug,
because it will be the one line that refuses to grow. The header chrome and SVG
labels opt out on purpose — see §5.9 and §6.

### The three-state theme problem

Three viewer states, not two: explicit light, explicit dark/manim, and system
default with **nothing stamped** on the root.

```css
:root { /* the complete light palette — every token */ }

@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) { /* dark tokens only */ }
}

:root[data-theme="dark"]  { /* dark tokens  */ }
:root[data-theme="manim"] { /* manim tokens */ }
```

1. **Every token gets its value on bare `:root` first.** A colour defined only
   inside a media or `[data-theme]` block is undefined in the unstamped state —
   this is the classic unreadable-page bug.
2. **Style components through tokens only.** Never write a colour inside a theme
   block that isn't a token definition.
3. **`body` sets an explicit background from a token.**
4. **Later theme blocks must redefine every token an earlier one set**, because
   `:root:not([data-theme="light"])` and `:root[data-theme="manim"]` have equal
   specificity and source order decides.
5. **A theme choice must beat the OS in both directions** — that is what the
   `:not([data-theme="light"])` guard is for.

---

## 8. Motion

Motion carries information, states presence, or marks a moment. Nothing moves
for decoration.

**This rule loosened deliberately.** It previously forbade page-load entrances
and any looping outright, and under that rule the rep panel sat as an empty grey
rectangle until clicked — the page's single most persuasive element, showing
nothing, on a page whose job is to be trusted enough to take $19. A demo that
does not look alive is not a neutral choice. What survives from the old rule is
the ban on motion that carries nothing: no parallax, no scroll-jacking, no
reveal-on-scroll applied to a paragraph because it was there.

| permitted | why it is not decoration |
|---|---|
| a diagram drawing itself in the order the system works | the order *is* the content |
| an idle loop on a component that is waiting for input | states "this is live, and it is yours to start" |
| a boot sequence on the demo | shows the topology before the sequence uses it |
| a state transition the reader caused | confirms the system heard them |
| a result arriving as a sequence | the order of the reveal is the reward |

### Curves

Two, defined as tokens, and no others:

```css
--ease-out:    cubic-bezier(0.16, 1, 0.3, 1);   /* arrivals, settles hard */
--ease-in-out: cubic-bezier(0.65, 0, 0.35, 1);  /* ambient loops */
```

**Nothing overshoots and nothing bounces.** Springy motion reads as a toy; this
page is asking for money. Where something scales in, it scales *down* to rest
(1.06 → 1), never up through it.

### Durations

| what | ms |
|---|---|
| hover, tap feedback | 150 |
| fade | 420 |
| line draw | 550–780 |
| shutter, stamp | 240–340 |
| ambient loop | 2600–3600 |

Stagger between siblings is 70–90ms for lists, 100–300ms for large elements.
Faster than 70ms reads as a glitch, slower than 300ms reads as a wait.

### Attracting attention without looking cheap

The free book is the distribution — how a stranger learns the material is good
before being asked for $19 — so its calls to action have to pull the eye.

**They do it without a single loop.** An earlier version of this section
permitted blinking chips, pulsing rings and a shaking floater. That was wrong
and it looked it. Looping motion reads as *desperate*, which is expensive on a
page asking for money, and the eye filters repeating movement out within seconds
anyway — so it costs credibility and stops working.

Attention comes from three things that do not decay:

1. **Solid colour.** An accent block on a paper ground is already the loudest
   thing in the viewport. Moving it only makes it look unsure of that.
2. **A number instead of an adjective.** *"51 chapters, free"* beats *"read the
   free book"*: a number is a reason and is read faster than a sentence.
   *"Free"* alone is only a claim.
3. **One decisive movement on arrival.** The book button fills with accent left
   to right, once, when it first scrolls into view, then holds. The floater
   slides up once, then holds.

That last one is the rule that makes the page cohere: **this page's motion
vocabulary is drawing.** The diagram draws itself, the chart draws itself, so a
button that fills itself belongs to the same language. A button that blinks
belongs to a different and worse one.

The single permitted exception is an idle indicator *inside* a component that is
waiting for input — the rep panel's pulse — and it stops the moment that
component has something real to say. Nothing that asks for a click may loop.

### Ambient motion has rules

An idle loop must be slow, low-contrast, and must **stop the moment the
component has something real to say** — the rep's pulse dies when the rep
starts, because from then on the diagram is speaking and ambient motion would
compete with it. Only one thing on the page may loop at a time.

### SVG dash animation

Animate `stroke-dashoffset` against `pathLength="100"`, never against a measured
or `var()`-derived length. A keyframe value like
`calc(-1 * (var(--len) + 26))` **does not interpolate** — the browser cannot
resolve the custom property at parse time and falls back to a discrete jump, so
the thing teleports instead of travelling. `pathLength` also lets one set of
keyframes drive both diagram widths.

### Reduced motion

`prefers-reduced-motion: reduce` sets `animation: none` on every one of these and
removes transitions. Every animation on this page decorates a state that is
already correct, so the end frame is the truth and it simply arrives instantly.
Ambient loops go to opacity 0 rather than freezing mid-travel.

---

## 9. Accessibility

Non-negotiable, and mostly already satisfied by the rules above.

- **Text contrast ≥ 4.5:1**; large text ≥ 3:1. `--on-accent` is near-black
  because white on the orange fails (§2.3).
- **`--line-strong`, not `--line`, for any border that is the only visual marker
  of a control.** Decorative hairlines keep the low-contrast token deliberately.
- **Visible focus everywhere:** `:focus-visible { outline: 2px solid var(--accent);
  outline-offset: 2px }`. Never remove an outline without replacing it.
- **Every control has an accessible name.** Icon buttons carry `aria-label` that
  states current state *and* action: `"Theme: Blueprint. Switch theme"`.
- **Live regions** for content that changes without a reload — the rep's
  narration line is `aria-live="polite"`.
- **Reflow at 320px** with no horizontal page scroll.
- Diagrams carry `role="img"` and a one-line `aria-label`. *Known gap, inherited
  from the book: no long description of diagram structure. Satisfies 1.1.1;
  gives screen-reader users the gist rather than the shape.*

---

## 10. Voice

The interface writes the way the book writes: plainly, and never overselling.

- Say what a control does, then confirm it happened in the same words.
- Name the uncomfortable thing rather than softening it. *"That's it. It's
  gone."* beats *"Diagram hidden."*
- Never claim something the product does not do. Where the demo is hand-built,
  the page says the demo is hand-built.
- No exclamation marks, no congratulation for ordinary actions, no emoji as
  section markers.
- Errors say what went wrong and what to do. No apologies.
- **No em dashes anywhere in visible copy.** Use a full stop, a comma, or a
  colon, whichever the sentence actually needs. The em dash was doing three
  different jobs on this page and reads as machine-written; picking the right
  mark each time forces the clause to be either a real aside or a real sentence.
  For labels and buttons, a middle dot separates (`watch the rep · 13s`) and a
  preposition joins (`Reserve a seat for $19`). Code comments are not copy and
  are exempt.

---

## 11. Conformance checklist

Before shipping a screen:

- [ ] Zero border-radius, zero box-shadow, all borders 1px
- [ ] Exactly one accent element as primary action; accent used nowhere decorative
- [ ] Every colour from a token; no hex in a component
- [ ] Every token defined on bare `:root`; all three themes checked
- [ ] Three type registers respected — no serif chrome, no mono prose
- [ ] Chrome lowercase, prose sentence case
- [ ] Text contrast ≥ 4.5:1 in all three themes
- [ ] Visible focus on every interactive element
- [ ] Icon buttons have state-and-action `aria-label`
- [ ] 320px reflow with no horizontal scroll
- [ ] `prefers-reduced-motion` delivers the same information without motion
- [ ] Any diagram exists in both wide and narrow variants
- [ ] Every reading-text rule is `calc(Npx * var(--fs))`, checked at Largest
- [ ] Nothing that asks for a click loops, blinks or shakes (§8)
- [ ] No two accent fills share a viewport, at any scroll position
- [ ] Motion verified by pausing it at a frame and looking, not by reading the DOM
