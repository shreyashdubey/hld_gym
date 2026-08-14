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
