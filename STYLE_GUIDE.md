# HLD Gym — Content Style Guide (contract for chapter authors)

Every chapter ships two files in `src/chapters/`:
1. `<id>.html` — the article body (fragment only, no `<html>/<head>/<body>`)
2. `<id>.quiz.json` — the quiz

`<id>` comes from `src/toc.json` (e.g. `p1c06`). Follow this guide exactly; `build.py` rejects violations.

---

## 1. Voice — the whole point of this book

Write like an experienced engineer explaining to a smart friend over chai. The reader is a working developer with 3 years of experience who has never been taught this properly.

**Rules:**
- Simple words. Short sentences. If a 12-year-old couldn't follow the sentence structure, rewrite it. Technical terms are fine — but define every term in plain words the first time it appears, in the same sentence or the next one.
- Second person. "You have a server. It's doing fine. Then your app goes viral."
- Never write like a textbook. Banned openers: "In this chapter, we will…", "X is defined as…", "It is important to note…". Just start with the problem.
- **Problem before solution, always.** Never introduce a tool and then explain why it exists. Create the pain first, let the reader feel stuck, then reveal the fix. The reader should think "…so how do you fix THAT?" right before you tell them.
- **Hooks between sections.** End sections with tension when natural: "This works beautifully. Until one of your users is Cristiano Ronaldo. Then it melts. Here's why."
- Numbers make it real. "Reading from RAM is like grabbing a pen from your desk. Reading from disk across a network is like driving to another city for the pen."
- It's okay to be funny occasionally. Never at the cost of clarity.
- No hedging filler ("basically", "essentially", "simply put").

**Every major concept needs BOTH:**
- an **analogy** from ordinary life (`.analogy` box) — post office, restaurant kitchen, library, traffic, hostel mess. Keep analogies honest: say where the analogy breaks if it does.
- a **war story** (`.story` box) — a real company, the real incident/design, in genuine detail: what they had, what broke or what forced the change, what they built, what it cost/saved. 4–10 sentences of substance, not "Netflix uses caching." Good sources: Discord's Cassandra hot partitions, Instagram's ID generator, Twitter's fanout redesign, Figma OT→CRDT, Netflix Open Connect, Stripe idempotency keys, Amazon's Dynamo paper origins, WhatsApp's 50 engineers, GitHub's MySQL failover incident, Cloudflare outage postmortems. Real, verifiable stories only — if unsure it's true, pick a different story.

## 2. Chapter anatomy (in order)

1. **Cold open** (no heading): 2–4 paragraphs. A concrete scenario that creates the problem this chapter solves. Never start with a definition.
2. **Sections** (`<h2>`, `<h3>` only). Build the topic problem → solution → new problem → … Each `<h2>` section: prose + analogy/story/diagram/table as fits.
3. **`.lens` box** ("At the whiteboard"): how this topic is actually probed at senior level; what a passing answer sounds like; 2–3 verbatim-style probe questions an interviewer would ask.
4. **`.feynman` block**: one prompt ("Explain X to a junior in 4–5 sentences") + a hidden model answer. The model answer is the gold standard of simple explanation.
5. **Exercises**: 3–5 `.exercise` blocks — estimation drills, "sketch this design", "what breaks if…" — each with a hidden worked answer.
6. **`.takeaways`**: 5–8 bullet summary, each bullet a full sentence that stands alone.

Problem chapters (Part 3) instead follow: cold open → requirements → estimation → API → high-level design → deep dives (mark the hardest with `.crux`) → failure modes + ops → "what the interviewer probes next" (in `.lens`) → trade-off table → feynman → exercises → takeaways.

Length target: 2500–4500 words of body prose (Part 3 chapters toward the high end). Comprehensive beats short; boring is the only sin.

## 3. HTML components (use ONLY these)

Allowed elements: `p, h2, h3, ul, ol, li, strong, em, code, pre, table, thead, tbody, tr, th, td, figure, figcaption, svg (+children), details, summary, div, span, dfn, br, blockquote`.
No inline `style=`, no `<img>`, no external URLs anywhere (build fails).

Boxes — exact structure:
```html
<div class="box analogy"><div class="box-tag">Analogy</div>
  <p>…</p>
</div>
<div class="box story"><div class="box-tag">War story — Discord</div>
  <p>…</p>
</div>
<div class="box lens"><div class="box-tag">At the whiteboard</div>
  <p>…</p><ul><li>…probe…</li></ul>
</div>
<div class="box crux"><div class="box-tag">The crux</div>
  <p>Why this is the hardest part…</p>
</div>
```

Feynman block (engine injects the textarea; `data-key` must be unique, `<id>-f1`):
```html
<div class="feynman" data-key="p1c06-f1">
  <p class="fey-prompt">Explain cache invalidation to a junior in 5 sentences.</p>
  <details class="fey-model"><summary>Compare with a model answer</summary>
    <p>…model explanation…</p>
  </details>
</div>
```

Exercise:
```html
<div class="exercise">
  <div class="ex-q"><p>…question…</p></div>
  <details><summary>Answer</summary><p>…worked answer…</p></details>
</div>
```

Takeaways:
```html
<div class="takeaways"><div class="box-tag">Takeaways</div><ul><li>…</li></ul></div>
```

Tables: plain `<table>` with `<thead>`. Great for trade-offs and latency numbers.

## 4. Diagrams (inline SVG, theme-safe)

Every chapter needs 2–5 diagrams. Boxes-and-arrows, kept simple. Wrap in:
```html
<figure class="diagram">
  <svg viewBox="0 0 720 300" role="img" aria-label="one-line description">…</svg>
  <figcaption>Caption that explains what to notice.</figcaption>
</figure>
```
Rules:
- Only use CSS classes for color — never hardcoded fills/strokes except `fill="none"`. Classes: `dg-node` (component box: rect), `dg-node-alt` (highlighted box), `dg-edge` (line/path/arrow), `dg-txt` (text), `dg-txt-s` (small/label text), `dg-zone` (dashed grouping rect), `dg-bad` (failure-red element), `dg-good` (green element).
- Arrowheads: end paths with a small triangle `<path class="dg-edge-fill" d="…"/>` or reuse `marker` id `arrow` (defined once globally by the engine — just add `marker-end="url(#arrow)"` to edges).
- Text: `<text class="dg-txt" x=… y=…>` — keep labels short; font is set by CSS.
- viewBox width 720, height as needed (200–420). Nothing outside the viewBox.

### Stepped diagrams (optional)

Every diagram already animates: edges draw themselves and nodes fade in left-to-right when the reader scrolls to them. That is automatic — author nothing.

If a diagram tells a **sequence** (a request hopping through services, a migration running in phases, a failure and its recovery), wrap each stage in a `<g data-step="N">` and the engine adds a stepper the reader can walk through:

```html
<g data-step="1" data-step-label="Client asks the app server for permission">
  <rect class="dg-node" …/><text class="dg-txt" …>Client</text>
  <line class="dg-edge" … marker-end="url(#arrow)"/>
</g>
<g data-step="2" data-step-label="Server signs a short-lived slip">…</g>
```

- Steps are cumulative: step 3 shows everything from steps 1–3.
- Anything left outside a `<g data-step>` is scaffold — always visible. Use it for lifelines and frames.
- `data-step-label` is the line of narration shown beside the controls. Write it as a sentence that teaches, not "Step 2".
- Only add steps where order is the lesson. A diagram that is one static picture should stay one static picture.

## 5. Quiz JSON — `<id>.quiz.json`

```json
{
  "chapter": "p1c06",
  "items": [
    {
      "id": "p1c06-q01",
      "level": 1,
      "type": "mcq",
      "tag": "eviction",
      "q": "Your cache is full and a new item arrives. What does LRU evict?",
      "options": [
        {"t": "The item that was added first", "correct": false,
         "why": "That's FIFO. LRU doesn't care when an item arrived — it cares when it was last used."},
        {"t": "The item that hasn't been read or written for the longest time", "correct": true,
         "why": "Right. LRU = Least Recently Used. The item nobody has touched for the longest time is the one least likely to be needed next, so it goes."},
        {"t": "A random item", "correct": false,
         "why": "Random eviction exists (Redis offers it) but it's not LRU. LRU tracks usage recency."},
        {"t": "The largest item", "correct": false,
         "why": "Size-based eviction is a different policy. LRU only looks at recency of use."}
      ]
    }
  ]
}
```

Rules:
- Counts per chapter: **8–10 level-1** (recall), **8–10 level-2** (apply to a scenario), **6–8 level-3** (senior judgment: commit-and-justify, what-breaks-at-10x, failure probes). 24–28 total.
- `type`: `"mcq"` (exactly one correct) or `"multi"` (2+ correct; use sparingly, ≤3 per chapter).
- **Every option needs `why`** — wrong options explain the misconception in a friendly way ("That's FIFO, and here's the difference…"), never just "Incorrect." The `why` for the correct option re-teaches in one or two sentences. This is a hard build check.
- L2/L3 questions are scenarios: "You run a photo app with 10M daily users. Feed reads spike at 9pm…" Options are decisions, and each `why` explains the trade-off.
- L3 style matches senior grading: right answer = the committed, justified choice; wrong answers = option-listing, buzzwords, over-engineering, happy-path-only thinking — and each `why` says WHY that reads junior.
- 4 options per mcq (3 ok if natural). `tag` = short concept slug for review-queue display.
- IDs sequential `q01…qNN`, globally unique via chapter prefix.

## 6. Accuracy

- No invented numbers, quotes, or company stories. If a war story's details are fuzzy, use a different, well-documented one.
- Latency/throughput figures: use widely accepted orders of magnitude; round numbers.
- Technology claims must be current-ish (2024–2026): e.g., S3 is strongly consistent read-after-write since 2020; say so correctly.

## 7. Origins mode — the story-first layer

`/origins` is a second compiled view of the same 51 chapters. Every chapter opens on a **real, dated, sourced event** instead of an invented scenario, and the people, incidents, artifacts and consequences in that event become cards the reader earns by recall.

Chapters in `/origins` ship three extra files in `src/chapters/`, alongside the two every chapter already has. All three are optional; a chapter without them renders in `/origins` exactly as it does in `/book`.

1. `<id>.origin.html` — the story-first cold open, ≤260 words
2. `<id>.cards.json` — the deck, 4 suits
3. `<id>.cite.json` — the source ledger

They ship **together or not at all**. `build.py` holds one direction of that: it rejects an `.origin.html` with no `.cards.json`, and an `.origin.html` with no `.cite.json` — a card's provenance is the story that produced it, and a story with no ledger is a claim. The other direction is on you: a `.cards.json` with no story still builds, and a `.cite.json` with no story is never even read.

The story **replaces** the chapter's fictional cold open in `/origins`. Do not delete the fiction from `<id>.html` — `/book` still renders it, and `/origins` swaps it out at render time. If a later paragraph of the chapter refers back to the fictional scenario ("that queue you were staring at"), that reference is now dangling in one of the two views, and the chapter file does need an edit.

### The nine rules

Each is checkable by the author without a judgement call. The reasoning is part of the rule: an author who does not know why O2 exists writes an achievement story.

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
chapter's `.cite.json`. The build enforces the floor, not the rule. Four conditions, all on
the story's own prose: it must carry at least one `data-cite` key; at least one of those keys
must sit on a `<span class="fact">`; every key you write must resolve; and at least one key
cited in the prose must be a primary source. Card `cite` keys satisfy none of the four — a
deck always cites something, so counting it would make the gate unfirable.

**At least one fact span, not all of them.** A `data-cite` on the box, or on a paragraph, or
attached to a clause rather than to a number, is legitimate and the build accepts it. Do not
contort a sentence to get a `.fact` span around it — the condition is only that a story
claiming to be sourced contains at least one citable fact that carries its source. If you are
following O5 you clear this without noticing, because every date, number and quoted string
already gets a `.fact` span.

Whether a *particular* date is cited is not machine-checkable and is yours to hold.

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

O5's floor is per-chapter and the rule is per-fact, so read the two apart: the build can tell that your story cites nothing at all, and that a key you wrote names no source, and that nothing the story cites is primary. It cannot tell that you left a date uncited. See "What `build.py` checks" for the exact line between what the build holds and what you hold.

### Running O1, and failing it honestly

O1 is the gate. It is what stops this mode becoming a book of fun facts, and it is the entire defence of putting a story in the opening slot at all — a story that derives the kernel is not a seductive detail, it is the explanation.

**The test, in order:**

1. Write the chapter's kernel down in one sentence, from `docs/kernels.md`, **before** you go looking for a story. A kernel you write after finding the story will bend to fit it.
2. Find the candidate event. Then write the counterfactual out loud: *if this story were deleted, what could the reader no longer explain?*
3. If the honest answer is "nothing — it is just interesting", the story is decoration. **Stop.**

"The reader would not know Lamport wrote it" is not an answer to step 2 — that is a fact about the story, not about the mechanism. A pass reads like: *without this, the reader cannot say why a fencing token has to be a monotonically increasing number rather than a lease.*

**If the chapter has no kernel.** `docs/kernels.md` carries one kernel per concept chapter — 26 of the 51. `p0c02` and the 24 Part 3 chapters have none, and only 12 of the Part 3 chapters appear at all, as a one-line crux in the table near the bottom of that file. Use the crux line as the kernel where there is one. Where there is neither, write the kernel sentence yourself from the chapter's `.crux` box and its `.takeaways`, put that sentence in your commit message, and run O1 against it. A missing kernel is not permission to skip O1.

**The failure path.** A chapter that fails O1 writes no sidecars — no story, no cards, no ledger — keeps its fictional cold open, and records the reason:

```bash
python3 - <<'PY'
import json, pathlib
p = pathlib.Path("src/origins.json"); d = json.loads(p.read_text())
d["failed"]["<id>"] = "<one sentence: what was considered, and why it did not derive the kernel>"
p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
PY
```

**Failing is expected and it is a result, not a shortfall.** Recon put the survivors at roughly 18–22 of 51, and the true number is unknowable until every chapter has been tried. A `failed` entry is data: it is what lets the sell page print a real count instead of a promise. Forcing a story into a chapter that failed O1 manufactures precisely the seductive detail this design exists to prevent, and is the one outcome worse than an empty entry.

### The origin fragment

`src/chapters/<id>.origin.html` is a fragment under §3's rules, with two differences: `<img>` is permitted here and nowhere else, and the `origin` div classes are allowed. The whole file is exactly two blocks — the story, then the reader's turn — and nothing else:

```html
<div class="box origin"><div class="box-tag">Place, Year</div>
  <p class="origin-seam">…an optional one-line scene-setter, set in muted italic…</p>
  <p>…the story, ending on the constraint…
     <span class="fact" data-cite="key">the number</span>…</p>
</div>

<div class="feynman" data-key="p2c03-o1">
  <p class="fey-prompt">What do you think went wrong next? Write it before you read on.</p>
</div>
```

The `box-tag` is the seam signal required by O8: a place and a year, never "an aside" and never "fun fact". Where the event has no meaningful place, use the organisation and the year — "DEC SRC, 1989".

The second block is O3, and you author it: the engine renders a textarea into any `.feynman` block, autosaves it, and works with the gym switched off. The `data-key` is `<id>-o1`, not `<id>-f1` — the chapter's own Feynman block still exists further down and the two must not share a state key. Write **no** `.fey-model` here. The reveal is the chapter itself, which is the whole point of asking before it.

The engine drops everything before the chapter's first `<h2>` and puts this fragment there instead. So the last line of the story has to hand off cleanly to that heading: read the two together before you call the story finished.

Every date, number and quoted string goes in `<span class="fact" data-cite="key">`, where `key` names an entry in `<id>.cite.json`. A `data-cite` may hold several space-separated keys; each one must resolve. HTML comments are stripped before the build scans for citations, so a `data-cite` inside `<!-- … -->` does not count as one.

Images are permitted **only here**, and only as `<img src="assets/…" alt="…">` with a non-empty alt, pointing at a file that really exists in `src/assets/`. Nowhere else in the book.

§3's external-URL ban still holds, and it holds for this file: an `https://` anywhere in the fragment fails the build. Source URLs live in `.cite.json`, which is not scanned.

The **260-word limit** is counted over the whole file with tags stripped, so the `box-tag`, the `fey-prompt` and any `<figcaption>` all count against it. 260 passes, 261 fails.

### The card

`src/chapters/<id>.cards.json`, shaped `{"chapter": "<id>", "cards": [ … ]}`. One card per suit is the target.

```json
{
  "id": "p2c03-c1",
  "suit": "person",
  "title": "Leslie Lamport",
  "sub": "1989 · DEC Systems Research Center",
  "year": 1989,
  "body": "≤60 words on the face",
  "prompt": "the recall question the reader must answer to keep the card",
  "answer": "what a correct answer contains",
  "asset": "assets/lamport.svg",
  "cite": "lamport1998"
}
```

`suit` ∈ `person | incident | artifact | ripple`. `year` is an integer between 1800 and 2100, used by the timeline. `cite` is one key into `<id>.cite.json`. `asset` is optional; **everything else is required, `sub` included.**

| suit | what it holds |
|---|---|
| **PERSON** | a named human, the year, and what they were actually trying to do at the time — usually not the thing they became famous for |
| **INCIDENT** | the outage, breach or bug, with the date and the price tag in real money |
| **ARTIFACT** | the primary source the reader can open right now: paper + year + venue, RFC number, commit SHA, PR, CVE |
| **RIPPLE** | the consequence chain — this decision, made once, is why your cluster does X today |

Write the `prompt` first. If the prompt is answerable by reading the card, it is not a card. That gate is the whole reason cards exist: a fact scattered through a chapter for interest is the Harp & Mayer 1998 manipulation verbatim and measurably harms learning, while a fact the reader has to produce is retrieval practice. The same gate is what moves a portrait from decorative (Sung & Mayer 2012 put a famous face at d=−0.38) to instructive.

`asset` is optional and the honest default is to leave it out — a card with no picture is still a card, and the recall gate is what makes it work. If you do add one: it lives in `src/assets/`, it is a two-colour halftone in the theme's ink and paper like every other image in `/origins`, and its licence has to be public domain, CC0, CC BY, or CC BY-SA with the credit added to `src/template.html`. **A company gets its name set in the book's own type, never its real logo** — that line is *Toyota v. Tabari*, and it holds on every surface including the favicon and the OG image.

Card ids share the quiz id namespace deliberately, so the existing Leitner machinery grades a card with no new state. Cards are `<id>-c1…`, quiz items are `<id>-q01…`; the build does not check one list against the other, the naming convention is what keeps them apart.

O4 is checked by a person, so check it: read `<id>.quiz.json` before writing the deck, make sure every proper noun in the story is answerable on a card or in a question that already exists, and do not add a card that asks what a question already asks.

### The sidecar

`src/chapters/<id>.cite.json`. **Write this file before the prose**, so the prose can only claim what the ledger already holds.

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

`type` ∈ `paper | rfc | postmortem | blog | commit | pr | cve | book | talk | docs | oral-history`. Always required: `title`, `year`, `type`, `checked` — and `quote` as well, on any source of a primary type. `confidence: "secondary"` is the escape hatch for a fact only reachable through a secondary source.

`quote` is stored when you verify, not when you cite — roughly 15–20% of primary sources 403 later, and the stored string means a dead link never forces a re-hunt. The build requires it on every primary source, which is the same rule stated as a check. `unverified` is a real array and an empty one is a claim: anything you could not confirm goes in it, and **does not go in the prose**.

At least one source **cited in the story's prose** must be **primary**: `paper`, `rfc`, `postmortem`, `commit`, `pr`, `cve` or `oral-history`. A card cannot carry it for you — the build reads only the prose keys for this check, because the rule exists so the *story* rests on a primary source. A blog post or a vendor doc is a source, not evidence — vLLM's blog claims 24× where the SOSP paper says 2–4×.

Open every source yourself. Not a search snippet, the actual page or PDF. Five failure modes, all met live:

| failure | seen | guard |
|---|---|---|
| date drift from snippets | a search result gave "1651 UTC"; the source page says **15:51 UTC** | never source a timestamp from a snippet — open the page |
| apocrypha | the Dijkstra café story is real, but is a **2001 recollection** of a 1956 morning | write "Dijkstra told an interviewer in 2001…", never "in 1956 Dijkstra sat down…" |
| conflated timelines | "Chaos Monkey was built after the April 2011 EBS outage" — Netflix described it running on 2010-12-16 | check the earlier bound, not just the later one |
| venue drift | aggregators index the Kafka paper as DEBS'11; the PDF says **NetDB'11** | cite from the PDF, not the index |
| vendor PR as history | vLLM's blog claims 24×; the SOSP paper says 2–4× | prefer the peer-reviewed number and say which you used |

### Claiming a subject — the O6 registry

`src/origins.json` is the claim ledger. Read it before you choose a subject and write to it when you have one.

- `claimed` maps a subject slug to the chapter that owns it: `"knight-capital-2012": "p2c11"`. Anything listed is unavailable.
- `failed` maps a chapter id to a one-sentence reason it did not pass O1.
- `proposed`, where present, is a central allocation of one candidate subject per chapter, made in one pass so 51 parallel authors are not racing on a uniqueness constraint. It proposes; O1 still decides, and only an author who has read the chapter and opened the sources can run O1.

Claim it once the story is written and the build is green:

```bash
python3 - <<'PY'
import json, pathlib
p = pathlib.Path("src/origins.json"); d = json.loads(p.read_text())
d["claimed"]["<subject-slug>"] = "<id>"
p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n")
PY
```

The slug is lowercase, hyphenated, and carries the year where the subject is an event: `knight-capital-2012`, `dijkstra-shortest-path-1956`.

Sixteen subjects are already used two or three times in the existing war stories — Knight Capital, Stripe idempotency, Kafka/Kreps, the February 2017 S3 outage, Krikorian and Lady Gaga among them. Those are the worst possible openings even though they are unclaimed here: a chapter opening on a subject the book already tells twice teaches the reader that the book is short of material. Prefer a subject the book has never used at all.

### What `build.py` checks

Everything in this table is an error that stops the build, unless it says warning.

| check | rule |
|---|---|
| companion files | an `.origin.html` with no `.cards.json`, or with no `.cite.json`, fails |
| word count | tag-stripped `.origin.html` must be ≤260 words |
| `<img>` | origin fragments only; `src` must start `assets/`; `alt` must be non-empty; the file must exist in `src/assets/`. The tag and its attributes are matched case-insensitively |
| `assets/` references | in an origin fragment, every `src=`/`href=` beginning `assets/` — plus every card `asset` — must resolve to a real file inside `src/assets/`. A path that climbs out with `../` is rejected by name. The chapter's own `.html` is not scanned for these; it has no need, since `<img>` is banned there |
| `style=` and `on…=` | rejected in any fragment. The event-handler check is case-insensitive, so `onClick=` fails too |
| `https://` | rejected in any fragment, `.origin.html` included |
| tags | §3's allowlist, plus `img` in origin fragments |
| `data-key` | every Feynman `data-key` must start with the chapter id. Use `<id>-o1` in the origin fragment; `<id>-f1` is the chapter's own and the two must not collide |
| div classes | an unknown class is a **warning**. Origin and card classes already known: `origin`, `origin-seam`, `origin-body`, `card`, `card-face`, `card-back` |
| JSON shape | `cards` must be a list; `sources` must be an object; `unverified`, if present, must be a list |
| card ids | must start with the chapter id; unique within the file |
| card fields | `suit` one of the four; `year` an integer 1800–2100 (a JSON `true` does not count as one); `title`, `sub`, `body`, `prompt`, `answer`, `cite` all non-empty; `body` ≤60 words; `asset`, if present, starts `assets/` |
| `data-cite` keys | every key in the fragment, and every card `cite`, must name a `sources` entry. Keys inside an HTML comment are ignored, because a citation in a comment is not a citation |
| the citation gate | the **prose** must yield at least one `data-cite` key — an `.origin.html` with no `data-cite` at all, or only an empty `data-cite=""`, or only one inside an HTML comment, fails. Card `cite` keys do not count toward this gate |
| a cited fact | at least one of those prose keys must sit on a `<span class="fact">`. **At least one, not all** — a `data-cite` elsewhere in the fragment stays legal, it just cannot be the only one. `<p data-cite="k">` alone fails, and gets its own message, distinct from citing nothing at all. The class is matched inside a multi-class attribute and the attribute order does not matter |
| source fields | `type` one of the eleven; `year` an integer 1800–2100; `title` non-empty; `checked` matching `YYYY-MM-DD`; `quote` non-empty on every primary-type source |
| primary source | at least one source cited **in the prose** must be of a primary type. A card citing the only paper does not satisfy it |
| year agreement | a year inside a `<span class="fact" … data-cite="key">` must equal that source's `year`. Attribute order does not matter |
| unused source | a source nothing cites is a **warning** |

**What it does not check, and you therefore must.** Three of the nine rules have no validator at all, one has a weaker one than it looks, and one field is unchecked:

- **O5** is per-fact; the build's gate is per-chapter. One `data-cite` on one `.fact` span satisfies it, so a story with nineteen uncited dates and one cited one passes. Nothing tells you which date you left uncited. The year-agreement check likewise fires only on a `.fact` span whose `data-cite` holds a single key. What the gate *no longer* accepts: card `cite` keys, which are excluded from both it and the primary-source check.
- **O2** — that the last sentence is a wall and not a prize — is read by a person.
- **O4** — that every proper noun is answerable on a card or in an existing quiz item — is read by a person.
- **O6** — that your subject is unclaimed — is read by a person, against `src/origins.json`.
- The sidecar's own `chapter` field is never compared against its filename. Write it correctly anyway; the cards file's is checked and the inconsistency is not a licence.

The whole mode is worth nothing if those are not held, which is why Task 16 exists and why the agent that verifies a chapter is never the agent that wrote it.
