<!-- BEGIN:nextjs-agent-rules -->

# This is NOT the Next.js you know

This version has breaking changes — APIs, conventions, and file structure may all differ from your training data. Read the relevant guide in `node_modules/next/dist/docs/` (resolved from this file's directory; in monorepos the `next` package may not be visible from the repo root) before writing any code. Heed deprecation notices.

This block is written and re-added by `next dev` — verify at `node_modules/next/dist/server/lib/generate-agent-files.js`. Removing it from a diff only re-creates the uncommitted change; committing it with your work keeps the tree clean.

<!-- END:nextjs-agent-rules -->

# the sell page — agent guide

## Read order for a fresh session

1. **This file.**
2. `PROGRESS.md` — the last 3 entries, then the **Open** list at the bottom.
3. `SYSTEM.md` — §1 (two sites, one deployment), §2 (the rep loop), §8 (deploy),
   §9 (what is deliberately absent).
4. `DESIGN-SYSTEM.md` — only when touching anything visual.

Do not re-derive decisions recorded in those files. If one is wrong, fix the
file in the same commit as the code.

## What this is, in 30 seconds

Live at **https://hld-gym.vercel.app/** since 2026-08-17.

A presell page for a **30-day system design sprint** — the whole 51-chapter book,
197 reps and 450 reels — $19, starting 1 September
2026. It carries one playable rep: a diagram teaches itself, **locks**, you
rebuild it from memory, get scored, then an interviewer takes the answer apart.

The page exists to measure one thing: **will a stranger pay before the product
exists.** Payments are the metric. Signups are not.

Context: this is the Project Shipyard S3 build, ending **9 September 2026**.
Across three seasons only two builders ever got a paying customer; total program
revenue $450. **Three paying customers wins it.**

## One repo, three pipelines

| | URL | built by |
|---|---|---|
| the sell page (this directory) | `/` | `next build` → static export |
| the book, free forever | `/book` | `../build.py` |
| the reels | `/reels/*.mp4` | `../reel/make.sh` |

All three write into `../dist/`, which Vercel serves with no build command.
**Deploying is `git push` at the repo root.** See `../AGENTS.md` for the map.

The book is the distribution and the answer key. It stays free.

## Workflow — follow this

**Every unit of work gets an entry appended to `PROGRESS.md`.** One entry per
unit of work, not per commit, newest at the bottom, answering **what / why /
how**. Bugs get recorded with the symptom, because the symptom is what a future
session recognises.

If the work changed a decision documented in `SYSTEM.md` or `DESIGN-SYSTEM.md`,
update that document in the same commit. Documentation drift is the failure mode
this workflow exists to prevent.

## Commands

```bash
npm run dev            # localhost:3000
npm run build          # must end with ○ (Static)
npm test               # rubric tests
npm run lint           # must be clean
npm run publish:book   # copy the export into the book repo
npm run preview        # serve the combined site on :4173
```

Verify UI changes in a real browser before calling them done. The rep is the
product; do not assume it works. And **verify motion by pausing it at a chosen
frame and looking at the pixels** — "the animation is running" is measurable
from the DOM, "the animation is visible" is not, and they are different claims.

## Hard rules

- **No backend, no auth, no database** until someone pays. See `SYSTEM.md` §9.
  A login between a visitor and the payment link costs conversions.
- **`--exclude 'book/'` and `--exclude 'reels/'` stay in `publish:book`.** They
  are the only thing stopping `rsync --delete` from wiping a 4.6MB book and the
  reel encodes, both produced by different pipelines.
- **Diagram draw lengths come from endpoint coordinates, never
  `getTotalLength()`** — it returns 0 on a hidden element and breaks the
  wide/narrow swap. `SYSTEM.md` §3.
- **Dash keyframes animate against `pathLength`, never `var(--len)`.** A `var()`
  in a keyframe cannot resolve at parse time and silently degrades to a discrete
  jump. The opposite of the rule above, and both are right: `--len` is for
  transitions.
- **Swap selectors stay qualified** (`.stage svg.dgWide`). A bare class loses on
  specificity and renders both diagrams stacked, looking fine on desktop.
- **Every diagram exists wide (viewBox 720) and narrow (viewBox 320).** 11px
  labels in the wide drawing render at 4.5px on a phone.
- **`--on-accent` is near-black in every theme.** White on the orange is 3.1:1
  and fails. Do not "fix" it.
- **Nothing that asks for a click may loop.** Blinking and shaking CTAs were
  built, looked cheap, and were removed. Attention comes from solid colour, a
  number instead of an adjective, and one movement on arrival.
  `DESIGN-SYSTEM.md` §8.
- **Two accent actions never share a viewport.** One primary action per screen.
  A self-labelling box's strip (`.repTag`, `.priceH`) is a label, not an action,
  and sits above its own button by design (`DESIGN-SYSTEM.md` §5.1).
- **Every reading-text rule is `calc(Npx * var(--fs))`** or the text-size
  control cannot scale it.
- **The rubric matches stems, not exact words.** A false negative makes the
  grader look broken to the person deciding whether to buy.
- **Never claim the product does something it does not.** The page says the
  demo's follow-ups are hand-written and its score keyword-matched, because
  they are, and it says so inside the rep where the belief forms.
- **A number the visitor can check is checked against the artefact.** The reels
  are 45s files (`PACE = 3`), so the page says 45s and "about eleven minutes",
  not the 15s the story was written at. `grep -c '—' dist/index.html` must
  print `0`.
- **Each disclosure lives in one place, plus the *What exists today* answer,
  which is the summary.** Four reels: the fact line above the player.
  Hand-written probes and keyword score: the rep. Form-not-checkout: the hero
  hint and *What happens after you click*.
- Model answers are never rendered before the learner commits.

## Facts not worth re-deriving

- Tailwind was rejected deliberately; the design is a token set and plain CSS.
- Fonts are self-hosted at build via `next/font/google` — no runtime CDN.
- Gumroad is the payment rail for speed only; Dodo Payments is the long-term one
  (merchant of record, takes Indian sole proprietors, mentor on the Shipyard
  bench).
- `allowImportingTsExtensions` exists because Node's type stripping needs the
  explicit `.ts` on the test import.
- Theme and text size live on `<html>` (`data-theme`, `data-fs`) before React
  runs, which is why the toggles in `components/Toggles.tsx` use
  `useSyncExternalStore` rather than `useState`.
- `--fs` scales reading text only. The header chrome and the SVG labels opt out
  deliberately — see the comments on `.brand` and `.dgTxt`.
- `/book` 404s under `npm run dev` unless the `predev` symlink and the dev-only
  rewrite are both present; production resolves it from the filesystem.
- Learning styles do not replicate (Pashler 2008). Rep variety is justified by
  **output mode matching the interview**, never by input-modality preference.
- `../reel/` renders the reels and is **not part of the app**: standalone HTML
  outside `app/`, and its own `package.json` so Playwright stays out of this
  dependency tree. Its one rule is that the frame is a pure function of `t` — no
  CSS transitions or keyframes, or frame-stepped recording stops being
  deterministic. Check a cut with `node contact.mjs` before rendering every
  frame.
- The reel feed on the page swaps encode by theme: `light` gets the `paper` cut,
  everything else gets `dark`. A video is a rendered file, so it cannot adapt to
  a reader the way the rest of the site does — each palette is its own encode.
