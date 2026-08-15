# HLD Sprint — presell page

A one-page presale for the **30-day system design sprint**, with a playable rep
embedded in it. Built to answer one question and only one:

> Will anyone pay $39 for this before it exists?

The metric is **payments**. Not signups, not a waitlist — those measure
curiosity. Nothing here collects an account, because a login between a stranger
and the payment link only costs conversions.

## Two sites, one deployment

| | URL | built by | repo |
|---|---|---|---|
| the sell page (this directory) | `/` | `next build` → static export | `sell/` |
| the book, free forever | `/book` | `build.py` | repo root |
| the reels | `/reels/*.mp4` | `reel/make.sh` | `reel/` |

The sprint exports to static files and is copied into the book repo's `dist/`,
which Vercel already serves. **One Vercel project, one domain, one `git push` to
deploy** — from the *book* repo, which is the one Vercel watches.

## The rep

The demo is a real rep, hand-built for one topic (cache-aside read path, from
HLD Gym chapter `p1c06`):

```
idle      the diagram is alive: scaffold drawn, a pulse running App → Cache → DB
watch     it builds itself, 5 narrated steps, ~13s
lock      it disappears — no scrolling back, the panel shutters over it
rebuild   you reconstruct it from memory into a textarea
grade     scored against a 6-key rubric, rows ticking in, misses named
probe     3 follow-ups an interviewer would actually ask
reveal    what the chapter says, side by side with what you wrote
```

Everything is client-side. No LLM, no API keys, no per-visitor cost, nothing to
fall over if the page gets traffic. The follow-ups are written in advance for
this one diagram — **the page says so out loud**, because the product generates
them against the learner's real answer and the difference matters.

## Stack

- **Next.js 16** (App Router, TypeScript), `output: "export"` — no server
  features, so it ships as plain files
- **No Tailwind** — the Teenage Engineering design is a small token set carried
  over from the book, and plain CSS fights it less
- Fonts self-hosted at build time via `next/font/google` (Archivo / Literata /
  IBM Plex Mono), so there is no runtime CDN request
- **Python/FastAPI backend: not here yet.** It gets built after someone pays.
  The spend-instrument stack (FastAPI + Postgres + bcrypt sessions) ports over.

## Commands

```bash
npm run dev            # localhost:3000 — this app only
npm run build          # static export to out/
npm test               # rubric tests (node --experimental-strip-types)
npm run lint
npm run publish:book   # build + copy the export into the book repo
npm run preview        # publish, then serve the combined site on :4173
```

`npm run dev` cannot serve `/book` from the real book — that lives in the
file another pipeline builds. A `predev` script symlinks it in and a dev-only rewrite makes the
URL resolve, but **`npm run preview` is the only way to see exactly what
ships**.

## Before going live

1. **Create the Gumroad product** ($39, one-time), then set the link:
   ```
   NEXT_PUBLIC_BUY_URL=https://<you>.gumroad.com/l/<slug>
   ```
   Until it is set, the buy button is a dead `#buy` anchor on purpose — it is
   meant to be obvious that it is unwired.
   Gumroad is chosen for speed only (sign up and sell the same day, USD, works
   from India). Dodo Payments is the better long-term rail once there is a real
   product — lower fees, merchant-of-record, onboards Indian sole proprietors.
2. `npm run publish:book`, then commit and push **the book repo**.
3. Post the free book with the sprint offer at the bottom.

## Four things worth knowing before editing

**The diagram is drawn twice.** `DiagramWide` (viewBox 720) and `DiagramNarrow`
(viewBox 320) are both in the DOM and swapped by CSS at 720px. The wide drawing
squeezed onto a phone renders its 11px labels at **4.5px**; the narrow redraw
holds them at **10.2px**.

**Line draw lengths are computed from endpoint coordinates, not
`getTotalLength()`.** That is what makes the CSS swap safe — a measured length
returns 0 on the hidden variant, which is exactly what blocked this approach in
the book. Keep it that way.

**Dash *keyframes* are the opposite case: use `pathLength`, never `var(--len)`.**
A keyframe value containing `var()` cannot be resolved at parse time and falls
back to a discrete jump, so the animated element teleports instead of moving.
`--len` is right for transitions, wrong for keyframes.

**Watch specificity on the swap.** `.stage svg { display: block }` beats a bare
`.dgWide`, so the swap rules are qualified as `.stage svg.dgWide`. Getting this
wrong renders both diagrams stacked, and it looks fine on desktop.

## The rubric

`lib/rep.ts` grades free text against six keys, matching **stems** (`check\w*`,
`writ\w*`) rather than exact words, because a false negative on a correct answer
makes the grader look broken to someone deciding whether to pay.

It detects vocabulary, not knowledge, and the cost is measured: nonsense with
the right words scores 6/6, a fully reversed read path scores 6/6, and "I don't
remember" scores 4/6. Fine for exposing *omission* in a demo; replaced by LLM
grading before the product ships (designed and parked — see `PROGRESS.md`).
