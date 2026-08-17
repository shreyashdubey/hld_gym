# HLD Sprint — presell page

A one-page presale for the **30-day system design sprint**, with a playable rep
embedded in it. Built to answer one question and only one:

> Will anyone pay $19 for this before it exists?

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
watch     it builds itself, 5 narrated steps, ~12s
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

1. ~~**Create the reservation form.**~~ Done: `https://forms.gle/hkf5buMLV6PsAomp8`,
   wired into all four CTAs through `lib/links.ts`. To point them somewhere
   else without editing code:
   ```
   NEXT_PUBLIC_RESERVE_URL=https://forms.gle/<id> npm run publish:book
   ```
   The env var is read **at build time**: Vercel runs no build here, so it has
   to be in the environment for `publish:book`, not in the dashboard. With no
   variable set, the URL above is what ships.

   The form is the checkout for now. A response arrives, the payment link goes
   back by email, and the page says exactly that in *What happens after you
   click* — no checkout is claimed that does not exist. Gumroad is the rail for
   speed (sign up and sell the same day, USD, works from India); Dodo Payments
   is the better long-term one — lower fees, merchant-of-record, onboards Indian
   sole proprietors.
2. `npm run publish:book`, then commit and push **the book repo**.
3. Post the free book with the sprint offer at the bottom.

## The reservation form

Five questions and an email, in this order. The page promises "sixty seconds",
so every question is one tap except the email.

**Title:** Reserve a seat — 30-day System Design Sprint ($19)

**Description:** Five questions, sixty seconds. Your email is where the payment
link goes, and nothing else is ever sent there. I reply within 24 hours, and you
are charged nothing until you click the link. The sprint is not live until
1 September 2026, and if it slips you get a full refund.

**Q1. Email** — do **not** write this question. Turn on
*Settings → Responses → Collect email addresses → **Responder input***. Forms
then adds a required, format-validated email field at the top by itself.

The third setting, *Verified*, is the one to avoid: it forces a Google account
sign-in, which blocks every non-Google address and puts a login between a
visitor and a payment link — the same thing §9 of `SYSTEM.md` rules out for the
site. *Responder input* asks for no account at all.

The cost is that Google's field takes no help text, so "where the payment link
goes" moves into the form description, which is where it now is.

**Q2. When is your next system design interview?** — multiple choice, required.
Within 2 weeks · 2 to 6 weeks · 1 to 3 months · not scheduled, getting ready
first.

**Q3. What level are you interviewing at?** — multiple choice, required.
Senior (Meta E5, Google L5, equivalent) · staff or above · mid-level moving to
senior · startup, no level system.

**Q4. Where does it actually break for you?** — multiple choice + *Other*,
required. I blank at the whiteboard even on systems I have read · I can draw it
but cannot defend it under follow-ups · I do not know how deep to go · I have
never done a real system design round.

**Q5. Which part of this do you most want?** — multiple choice + *Other*,
required. Options are labelled with what is real, because the page's standing
rule applies to the form too:

| option | label |
|---|---|
| The lock: the diagram vanishes and I rebuild it from memory | ships 1 Sep |
| An interviewer that pushes back on my answer | ships 1 Sep |
| 15 reels a day, revision I can do on my phone | ships 1 Sep |
| A schedule I never manage: what I fail comes back sooner | ships 1 Sep |
| All 51 chapters covered in 30 days, not a sampler | ships 1 Sep |
| **Playground**: a coach I talk to live while I draw, that makes me think aloud and unsticks me | planned, not built |
| Grading by an LLM against what I actually wrote, not keywords | planned, not built |
| Reels with audio | planned, not built |
| A dashboard of every diagram I can and cannot rebuild | planned, not built |
| The same gym for low-level design (LLD) | planned, not built |

This is the only question that is not about the sale. Five of those ten are
unbuilt, and which one people reach for decides what gets built after the first
payment. They are listed in `SYSTEM.md` §1 under *Planned, not built*, and the
two lists have to stay in step: an option here that is not there is a promise
nobody has thought through. Cheapest roadmap research available, because it
rides along on a form the buyer was filling in anyway.

**Q6. If I send the payment link today, are you paying $19?** — multiple choice,
required. Yes, send it · probably, depends on your answers to my questions ·
just curious for now.

This is the question that sorts the list. Q2 and Q4 decide what the reply leads
with.

**Settings:** *Collect email addresses* → **Responder input** (see Q1) ·
*Limit to 1 response* off, since it would force a Google sign-in too ·
confirmation message:

> Got it. The payment link comes to that address within 24 hours. Reply to it
> with any questions, I answer them myself. — Shreyash

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
