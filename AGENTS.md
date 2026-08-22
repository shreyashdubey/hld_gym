# HLD Gym — repo guide

One repo, four pipelines, one deployment.

```
build.py     src/       →  dist/book/index.html     the book, 51 chapters, free
                        →  dist/origins/            the same book, story-first
sell/        next       →  dist/                    the sell page, site root
reel/        scenes     →  dist/reels/*.mp4         the reel feed
playground/  pipecat    →  (not deployed)           the voice service, local only
                            ↑
                      Vercel serves this directory, with no build command
```

**Deploying is `git push` on this repo.** `vercel.json` sets
`outputDirectory: dist` and there is no build step, so whatever is committed
under `dist/` is what goes live. Nothing builds in the cloud.

That is also why `dist/` is committed rather than ignored, and why each pipeline
writes to its own subtree and never clears the others:

- `build.py` writes only `dist/book/` and `dist/origins/`. One pass, two
  outputs: the same 51 chapters, the same quiz, compiled twice. `/origins`
  additionally gets an `assets/` directory copied from `src/assets/` — the
  only images in the whole product.
- `sell`'s `publish:book` rsyncs its export to `dist/` with
  `--exclude 'book/' --exclude 'reels/' --exclude 'origins/'`. **Those three
  excludes are the only thing stopping `--delete` from wiping 4.6MB of book,
  the origins view and the reel encodes**, all produced by entirely different
  pipelines.
- `reel/make.sh` writes only `dist/reels/`.
- `publish:book` also carries a fourth exclude, `--exclude 'playground/'`, for
  a different reason than the three above: nothing would be *wiped* by dropping
  it, `out/playground/` would simply start landing in `dist/playground/` and
  go live on the next `git push`. It stays until someone deliberately decides
  Playground belongs on the sales page — see the note below and the design
  spec's "Deliberately unresolved". Whoever makes that call reverses this
  exclude on purpose, not by accident.

**The `playground/` *service* — the Python directory — writes nothing into
`dist/`.** It holds the OpenAI key, is not a build step, and is not part of
the deployment; the diagram above is talking about this half. Playground's
*browser* half is a different story and does not live in this directory at
all: `sell/app/playground/` is one of `sell`'s own routes, so `next build`
emits `out/playground/index.html` exactly like every other page on the site,
and `sell`'s `publish:book` would ship it to `dist/playground/`, public, on
the sales page — unless excluded, which it currently is (see above). Read
"one repo, four pipelines" as pipeline boundaries, not directory boundaries:
this is the one pipeline whose output is split across two directories.

## Where to look

| you are changing | read first |
|---|---|
| the sell page | `sell/AGENTS.md`, then `sell/SYSTEM.md` |
| a chapter | `STYLE_GUIDE.md`, exemplar `src/chapters/p0c01.*` |
| an origins story | `STYLE_GUIDE.md` §7, then `docs/superpowers/specs/2026-08-22-origins-design.md` |
| a reel | `reel/` header comments; `docs/kernels.md` for the source material |
| anything visual | `sell/DESIGN-SYSTEM.md` |
| the voice service | `playground/README.md`, then `docs/superpowers/specs/2026-08-21-playground-design.md` |

`sell/PROGRESS.md` is the dated log for the whole product. Every unit of work
gets an entry: what shipped, why it was built that way, how it works. Bugs are
recorded with the **symptom**, because the symptom is what a future session
recognises.

## Commands

```bash
python3 build.py              # book → dist/book/ and dist/origins/ (--check validates only)
cd sell  && npm run preview   # build the sell page and serve the whole site on :4173
cd reel  && node preview.mjs  # regenerate the reel review pages
cd reel  && ./make.sh 02 dark # render one reel: master here, web encode into dist/reels/
```

`npm run dev` serves the sell page alone — `/book` and `/reels` are files this
repo's other pipelines produce, and the dev server does not know about them.
`npm run preview` is the only way to see exactly what ships.

## Rules that outlive any one session

- **Never claim the product does something it does not.** The page says the
  demo's follow-ups are hand-written, and that four reels exist rather than the
  450 the sprint promises, because both are true today. The rule covers the
  reservation form too: its roadmap question labels every unbuilt option
  **planned, not built**.
- **No backend, no auth, no database until someone pays** — with one
  exception, and it proves the rule rather than breaking it. Playground
  (`playground/server.py`'s `mode=playground`) gates on a Google sign-in,
  added 2026-08-22, because it is not a login between a visitor and a
  payment link: it is a metered service that spends real OpenAI credit per
  minute on an endpoint anyone on the internet could otherwise reach, with
  no visitor and no payment link anywhere near it. `mode=dictation` has no
  such cost shape (no LLM, no TTS — see the design spec) and stays
  completely open, on purpose. The sell page itself still has no backend, no
  auth, no database.
- **Never publish work as an Artifact.** The claude.ai account is shared, so
  anything published lands in a gallery other people browse. To show something
  visual, serve it locally: `python3 -m http.server` in the right directory.
- Learning styles do not replicate (Pashler 2008). Every format decision is
  justified by **output mode matching the interview**, never by a claim about
  how someone prefers to take information in.
