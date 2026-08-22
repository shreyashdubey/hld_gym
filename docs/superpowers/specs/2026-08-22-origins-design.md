# Origins — Design Spec

Date: 2026-08-22 · Status: approved by user (chat) · Companion to `2026-08-13-hld-gym-design.md`

A second readable view of the same 51 chapters, at `/origins`, in which every chapter
opens with a **true, dated, sourced story** instead of an invented scenario — and in
which the named people, incidents, artifacts and consequences become a deck of ~204
cards the reader earns by recall.

Free, ungated, and the sell page's new hook.

## What this is

| | today at `/book` | at `/origins` |
|---|---|---|
| cold open | invented second-person scenario | the real event that forced the mechanism into its shape |
| first interaction | read on | type what you think happened next, *then* read |
| the chapter body | 2,500–4,500 words, 197 diagrams | identical, untouched |
| the people | 43 named humans, buried mid-file | 204 cards, earned by recall, reviewed on the Leitner queue |
| the arc | 51 separate chapters | one timeline, 1950 → 2026 |

The book at `/book` does not change. `/origins` is a second compiled file over the same
chapter sources, the same 1,278 quiz items, and the same progress state.

### Why this exists

Two reasons, and they are different.

**The product reason.** `sell/AGENTS.md` states the page's job: measure whether a
stranger will pay before the product exists. The book is the distribution. `/origins` is
the most shareable artifact this repo can produce — it is the thing that makes someone
stop scrolling — and it costs no backend, no auth, no database, so the standing rule
survives intact.

**The learning reason, which is narrower than it first appears.** See "The evidence, and
what it changed" below. The short version: a true origin story in the opening slot is
supported *for this audience specifically*, and passive interesting-facts sprinkled
through a chapter are not supported at all. The design keeps the first and converts the
second into retrieval items.

## What exists today, precisely

Measured, not assumed:

- 51 chapters, ~284,000 words, 197 diagrams, 1,278 quiz items (461 L1 / 459 L2 / 358 L3).
- 125 `.story` boxes. **90%** name a year, 37% a month or day, 34% a named human, 69%
  cite an artifact. The corpus is already unusually well grounded.
- **No chapter opens with real history.** All 51 first paragraphs are invented
  second-person scenarios or a quoted interviewer prompt. 39 of 51 bury their first real
  dated event at 20–56% file depth. The opening slot is fully occupied by fiction, so
  nothing is a pure lift — but the slot is free.
- **16 subjects are already used 2–3 times** — Knight Capital ×3, Stripe idempotency ×3,
  Kafka/Kreps ×3, the February 2017 S3 outage ×2, Krikorian/Lady Gaga ×2. Roughly 30
  chapters cannot open on their own strongest story without repeating a company. This is
  the dedup tax and it is the reason O6 exists.
- `dist/book/index.html` is 4.6 MB, 1.61 MiB gzipped — 49% chapter HTML, 41% quiz JSON,
  8% base64 fonts. Headroom to a 2 MiB gz budget is ~403 KB: about 33 photographs, or
  ~151 authored SVGs. **This ceiling is the reason assets do not go in the HTML.**

## Architecture

### Files

Three new files per chapter, alongside the two that exist:

```
src/chapters/
  p2c03.html          unchanged
  p2c03.quiz.json     unchanged
  p2c03.origin.html   NEW   the story-first cold open, ≤260 words
  p2c03.cards.json    NEW   the deck: 4 suits
  p2c03.cite.json     NEW   the source ledger
src/assets/           NEW   portraits and marks, content-hashed filenames
src/origins.json      NEW   the dedup registry: subject → chapter that claimed it
```

`build.py` emits:

```
dist/book/index.html        as today, unchanged
dist/origins/index.html     story mode
dist/origins/assets/        images, served as files, cached immutable
```

A chapter with no `.origin.html` renders in `/origins` exactly as it does in `/book`.
The mode degrades to the current book rather than to a hole, so partial coverage is
always shippable.

### Why an assets directory rather than base64

The single-file property is worth real money — it is why the book survives being emailed
around — but it caps at ~33 photographs before the gz budget is gone, and every image
change re-downloads 4.6 MB. A sibling directory has no ceiling, caches independently, and
costs one `shutil.copytree`. The price is that `/origins` is no longer viewable over
`file://`. `/book` keeps that property; `/origins` is a deployed page and does not need it.

`build.py` enforces `src="assets/…"` — relative only, so the external-URL ban is not
weakened, merely made specific.

### Shared progress, and the bug it exposes

`/origins` and `/book` share `localStorage` under the existing `KEY = 'hldgym_v1'`
(`src/app.js:8`). This is deliberate: it is one book, one Leitner queue, one streak. A
card earned in `/origins` counts in `/book`.

It exposes a bug that already exists: `save()` writes the whole state object and nothing
listens for changes, so two open tabs clobber each other. Fix ships with this work — a
`storage` event listener that re-reads state. Three lines. It is a pre-existing defect,
not one this feature introduces, but this feature makes two tabs likely.

### Code changes

| file | change | size |
|---|---|---|
| `build.py` | read the three new sidecars; validate cards and citations; emit a second output; copy assets; allow `<img src="assets/…" alt="…">` in origin fragments only, with an attribute allowlist (there is currently none — `on*=` handlers are unchecked) | ~40 lines |
| `src/app.js` | mode flag; inject the origin open; card rendering + recall gate + Leitner wiring; `#cards` collection; `#timeline`; boss-round extension; the `storage` listener | ~300 lines |
| `src/template.html` | credits block for image attribution; mode flag | ~20 lines |
| `src/style.css` | card, timeline, halftone treatment, sketchbook surface | ~200 lines |
| `sell/package.json` | `--exclude 'origins/'` | 1 word |
| `sell/next.config.ts` | dev rewrite for `/origins`, mirroring the existing `/book` one | 2 lines |
| `vercel.json` | cache headers: `/origins/` must-revalidate, `/origins/assets/` immutable | 2 blocks |
| `sell/app/sitemap.ts` | the new route | 1 entry |

**The `--exclude 'origins/'` change lands first, before any content exists.**
`sell`'s `publish:book` is `rsync -a --delete --exclude 'book/' --exclude 'reels/'
--exclude 'playground/' out/ ../dist/`. Without a fourth exclude, the next publish
deletes `dist/origins/` entirely. Same trap the root `AGENTS.md` already documents for
`book/` and `reels/`; this is the third instance of it and it is the highest-consequence
single line in the whole build.

## The writing contract

New `STYLE_GUIDE.md` §7. Nine rules, each checkable by the author without judgement calls.

**O1 — the story must derive the kernel.** Take the chapter's kernel from
`docs/kernels.md`. Delete the story: can the reader still say *why the mechanism has this
shape*? If yes, the story is decoration and the chapter keeps its fiction. This is the
gate, and it is the only rule that can disqualify a chapter outright.

**O2 — end on the constraint, never the triumph.** The last sentence is the wall they hit,
not the prize they won. Lin-Siegler 2016 found struggle stories raised student grades and
achievement stories did not.

**O3 — the next element is the reader's input, not a paragraph.** The story ends, then a
textarea. Commit before reveal. The existing `.feynman` machinery (`src/app.js:669-682`)
already renders a textarea, autosaves to `S.feynman[data-key]`, and works with the gym
off — this is free and already shipped 51 times.

**O4 — every proper noun in the story is answerable.** On a card, or in an existing quiz
item. A name that is never asked about is decoration by definition.

**O5 — every date, number and quoted string carries `data-cite`.** Resolving to the
chapter's `.cite.json`. Build-enforced.

**O6 — no subject is reused across chapters.** `src/origins.json` holds the claim.
Because of the dedup tax, roughly 30 chapters must find a story that is not their
chapter's most famous one. This is a feature: it forces the book to widen its cast.

**O7 — ≤260 words, and the chapter's net prose must not rise.** The story *replaces* the
fictional cold open; it does not stack on top of it. Card text is not counted here — cards
are a separate surface with their own budget (≤60 words a face), because a card is
answered, not read past.

**O8 — signal the seam by topic, not by apology.** "Rotterdam, 1956." Never "as an aside"
or "fun fact". Wesenberg 2025: a topic signal recovers d=−.79 of the harm; an
irrelevance label does nothing measurable.

**O9 — carry the money and the consequence.** What it cost, in real currency. What it set
off downstream. This is the part that makes the story repeatable out loud, which is the
output mode the whole book is justified by.

## The deck

Up to 204 cards — 4 suits × the chapters that pass O1. **A chapter with no origin story
gets no cards**; the two ship together or not at all, because a card's provenance is the
story that produced it.

204 is therefore a ceiling, not a promise. See "The coverage question" below.

| suit | what it holds |
|---|---|
| **PERSON** | a named human, the year, and what they were actually trying to do at the time — usually not the thing they became famous for |
| **INCIDENT** | the outage, breach or bug, with the date and the price tag in real money |
| **ARTIFACT** | the primary source the reader can open right now: paper + year + venue, RFC number, commit SHA, PR, CVE |
| **RIPPLE** | the consequence chain — this decision, made once, is why your cluster does X today |

### Lifecycle

```
scroll past the card    →  appears greyed, uncounted
answer its prompt       →  colour, counted, enters the Leitner queue
fail it on review       →  greys again until re-earned
```

This is the reconciliation of the two card behaviours chosen in chat: discovered by
reading, kept by remembering.

**The gate is not cosmetic — it is the entire justification for the cards existing.**
Passive interesting-facts scattered through a chapter are the literal Harp & Mayer 1998
manipulation and there is no defensible version of them. A card the reader must produce
an answer for is retrieval practice, which is the highest-utility technique in Dunlosky
et al. 2013 and the thing `docs/learning-and-retention.md` identifies as missing.

A card whose prompt is answerable by looking at the card is not a card. Write the prompt
first.

### Two more views, no new content

- **`#cards`** — the collection. Earned cards in colour, unearned greyed, per-suit and
  per-part counts, gaps visible.
- **`#timeline`** — the same data on a 1950 → 2026 spine. This is the one thing 51
  separate chapters cannot teach: that these ideas arrived in an order, and each was a
  reaction to the last.
- Boss rounds interleave history cards with technical items through the existing
  `renderBoss` (`src/app.js:783`).

## The art

### One treatment over everything

Every image — photograph or drawing — is reduced to a two-colour halftone in the theme's
ink and paper. This is what allows a 1968 photograph and an authored portrait to sit on
the same page as one sketchbook rather than a scrapbook. It is also what makes the images
cheap: a halftoned 240px portrait is a fraction of a full-tone photograph.

### Sourcing, in order of preference

1. **Public domain / CC0 photograph.** No obligation. Best case.
2. **CC BY photograph.** Credit in the template's credits block.
3. **CC BY-SA photograph.** Usable, contrary to first analysis. Attribution cannot live
   in a chapter fragment (the URL ban), but it can live in `src/template.html`, which
   `build.py` does not validate. ShareAlike attaches to *adaptations of the photograph*,
   not to the page around it — so the halftoned derivative ships BY-SA and the book does
   not. A line in a credits page, not a contamination.
4. **Authored portrait**, fixed house template with three variable slots (hair
   silhouette, facial hair, eyewear) so fifty of them do not drift. This is the path for
   most working engineers whose postmortems the book cites — they have no freely licensed
   photograph at all.

**Companies: the name set in the book's own type. Never the real logo.** *Toyota v.
Tabari* is the clean line — the word "Lexus" was permitted, the stylised mark was not.
Never on `sell/`, never the favicon, never the OG image. It also reads better in a
sketchbook than a pasted-in brand asset.

### The honest caveat on portraits

The multimedia literature rewards **instructive** images — Sung & Mayer 2012, N=200:
instructive graphic d=+0.79, decorative d=−0.14, a famous person's face **d=−0.38**. And
every image class raised satisfaction ratings, so "readers loved the portraits" is
specifically the signal that means nothing.

A portrait sitting beside prose is decorative. A portrait that is the retrieval cue for a
fact the reader must produce is not. **The recall gate is what moves the portraits from
the negative column to the positive one**, which is another reason it is not optional.

Where a genuinely instructive image exists — a real latency histogram from a postmortem,
the actual Open Connect rack — it outranks any portrait and should be preferred.

## Verification

Hallucinated history would be fatal to a product whose standing rule is *never claim the
product does something it does not*. This section is not optional infrastructure.

### The sidecar

`src/chapters/<id>.cite.json`, mirroring the `<id>.quiz.json` convention:

```json
{ "chapter": "p2c03",
  "sources": {
    "github2018": {
      "type": "postmortem",
      "title": "October 21 post-incident analysis",
      "author": "Jason Warner",
      "year": 2018,
      "date": "2018-10-21",
      "url": "https://github.blog/…",
      "checked": "2026-08-22",
      "quote": "…exact string as it appears in the source…",
      "supports": ["43-second partition", "24h11m degradation"]
    }
  },
  "unverified": ["The specific hardware swapped during the maintenance window."] }
```

`type` ∈ `paper | rfc | postmortem | blog | commit | pr | cve | book | talk | docs |
oral-history`. Always required: `title`, `year`, `type`, `checked`.

Two fields earn their place:

- **`quote` is stored at verification time.** Sources 403 later; roughly 15–20% did
  during recon. Storing the string when you read it means a dead link never forces a
  re-hunt.
- **`unverified` is a first-class array.** The style guide's "if the details are fuzzy,
  use a different story" becomes a data field rather than a hope. An empty array is a
  claim; a populated one is honesty.

`confidence: "secondary"` is the escape hatch for a fact only reachable through a
secondary source.

### The build check

~18 lines in the existing per-chapter loop, offline, no network:

- every `data-cite` in the HTML resolves to a sidecar entry
- every story-open box carries at least one `data-cite`
- at least one cited source per chapter is of a **primary** type
  (`paper|rfc|postmortem|commit|pr|cve|oral-history`)
- a year appearing inside a `<span class="fact">` must match its source's year
- `checked` must be an ISO date; `year` must be an integer
- unused sidecar entries `warn`

Plus `test_cites.py`: one good sidecar passes, one bad sidecar produces exactly the
expected two errors.

Deliberately skipped: URL liveness and DOI resolution — link-checking needs the network
and must never live in `build.py`. Per-type required-field tables — add when a second
author joins.

### The human pass

**100% of dates and 100% of quoted strings get human eyes.** ~4 facts per chapter, ~200
total. The writing agent and the verifying agent must be different calls; a model
checking its own output is not a check.

Five failure modes, all encountered live during recon on four sample chapters:

| failure | example seen | mitigation |
|---|---|---|
| date drift from snippets | a search result gave "1651 UTC"; the source page says **15:51 UTC** | never source a timestamp from a search snippet — open the page |
| apocrypha | the Dijkstra café story is real, but is a **2001 recollection** of a 1956 morning | write "Dijkstra told an interviewer in 2001…", never "in 1956 Dijkstra sat down…" |
| conflated timelines | "Chaos Monkey was built after the April 2011 EBS outage" — Netflix described it running on 2010-12-16 | check the earlier bound, not just the later one |
| venue drift | aggregators index the Kafka paper as DEBS'11; the PDF says **NetDB'11** | cite from the PDF, not the index |
| vendor PR as history | vLLM's blog claims 24×; the SOSP paper says 2–4× | prefer the peer-reviewed number and say which you used |

## The sell page

`/origins` becomes the hook the page leads with. That reopens **14 standing claims** in
`sell/SYSTEM.md` §1/§9 — including "197 reps, one per diagram", "450 reels", "No drawing
canvas", "the diagram vanishes". Re-auditing them is part of this work, not after it.

Also: a `sitemap.ts` entry, an eleventh option on the reservation form's Q5, and the
rsync exclude.

The standing rule holds without exception: **the page may not claim a chapter has an
origin story until that chapter has one.** A live counter ("18 of 51 chapters traced") is
honest and is preferable to a claim that has to be walked back.

## The evidence, and what it changed

The proposal as first stated was: story openings, plus interesting facts peppered through
the chapter, plus photographs and logos. The literature splits that three ways.

**Supported.** Narrative structure is a large effect (Mar 2021: 150 effect sizes,
N=33,078, g=.55 combined, g=.72 for memory). Narrative-before-exposition specifically
benefits **knowledgeable** learners (Tobler 2024, *Learning and Instruction* 92) — which
is exactly this audience: mid-to-senior engineers reading self-paced. The
seductive-details harm is weakest under precisely these conditions: it reverses sign for
high prior knowledge (Magner 2014), is absent for high working-memory readers (Sanchez &
Wiley 2006), and is mitigated by unlimited study time (Rey 2012). Its effect size has
shrunk monotonically as meta-analyses got stricter — 0.30–0.48, then 0.37–0.41, and
**0.12–0.19** in the strictest.

**Not supported: passive nuggets through the chapter.** This is the Harp & Mayer 1998
manipulation verbatim, and their Experiment 4 found that highlighting, stated objectives
and signalling the main text all failed to repair it. **Converted, not dropped**: every
nugget becomes a recall-gated card, which turns it from an interruption into a retrieval
item.

**Not supported on its own: decorative portraiture.** d=−0.38 for a famous face. Fixed by
the same gate — a portrait that cues a fact you must produce is instructive.

**One position risk we are accepting knowingly.** Harp & Mayer found seductive detail at
the *beginning* is worse than at the end, and `docs/learning-and-retention.md` wants the
opening slot handed to the diagram, not to prose. O1 is the entire defence: a story that
derives the kernel is not a seductive detail, it is the explanation. If a chapter's story
cannot pass O1, the chapter does not get one — and O1 is expected to disqualify a
meaningful fraction.

## The coverage question

**Target: all 51. Expected: fewer. The honest number is not knowable before the hunt.**

This spec contains a tension worth stating rather than burying. O1 disqualifies any
chapter whose story does not derive its kernel, and O6 forbids reusing a subject another
chapter has claimed. Applied to the material as it stands today, recon put the survivors
at roughly 18–22 of 51.

That estimate is probably low, for one reason: it measured which chapters could open on
a story **already in the file**. O6 forces the opposite move — go and find a subject the
book has never used. Whether a non-duplicate, kernel-deriving story exists for the
remaining chapters is an empirical question that only searching answers, chapter by
chapter.

So the process is: try all 51, apply O1 honestly, record every failure with its reason
in `src/origins.json`, and report the real number. A chapter that fails keeps its
fictional cold open and renders normally.

**What must not happen:** forcing a story into a chapter that failed O1, which
manufactures exactly the seductive detail this whole design is built to avoid. The
counter on the sell page reads whatever the real number is.

## Sequencing

Chapter by chapter. Per chapter, two commits:

1. **Write** — `.origin.html`, `.cards.json`, `.cite.json`, assets, registry entry.
   `python3 build.py` green. Commit.
2. **Verify** — a separate pass, a different agent, human eyes on every date and every
   quoted string. Corrections and any `unverified` entries. Commit.

Infrastructure lands before chapter one: the rsync exclude, `build.py`, `app.js`, the
styles, and the registry. The first five chapters are the format test — if the shape is
wrong, it is wrong five times, not fifty-one.

Realistic cost per chapter: ~45 minutes of agent research and writing, ~10 minutes of
human fact-checking that cannot be delegated or compressed.

## Deliberately unresolved

- **What happens to the fictional cold opens that stay.** Chapters that fail O1 keep
  their invented opening, so the book carries two conventions. Whether that is an
  acceptable editorial state, or whether those chapters should instead open on their
  diagram per `learning-and-retention.md`, is a larger decision that this spec does not
  make and partly pre-empts.
- **Whether `/origins` eventually replaces `/book`.** If the format wins, maintaining two
  views is a cost with no upside. Not decided until at least twenty chapters exist.
- **Whether the timeline becomes a navigation surface** rather than a progress display —
  entering a chapter by clicking its year.
- **The reconstruction/drawing mode** that `learning-and-retention.md` argues for remains
  unbuilt and unspecified. `/origins` does not deliver it and should not be mistaken for
  it. `/sketchbook` is reserved for it.
