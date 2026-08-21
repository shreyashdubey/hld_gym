# HLD Gym — repo guide

One repo, four pipelines, one deployment.

```
build.py     src/       →  dist/book/index.html     the book, 51 chapters, free
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

- `build.py` writes only `dist/book/index.html`.
- `sell`'s `publish:book` rsyncs its export to `dist/` with
  `--exclude 'book/' --exclude 'reels/'`. **Those two excludes are the only
  thing stopping `--delete` from wiping 4.6MB of book and the reel encodes**,
  both produced by entirely different pipelines.
- `reel/make.sh` writes only `dist/reels/`.

**`playground/` writes nothing into `dist/`.** It is a service, not a build step,
and it is not part of the deployment.

## Where to look

| you are changing | read first |
|---|---|
| the sell page | `sell/AGENTS.md`, then `sell/SYSTEM.md` |
| a chapter | `STYLE_GUIDE.md`, exemplar `src/chapters/p0c01.*` |
| a reel | `reel/` header comments; `docs/kernels.md` for the source material |
| anything visual | `sell/DESIGN-SYSTEM.md` |
| the voice service | `playground/README.md`, then `docs/superpowers/specs/2026-08-21-playground-design.md` |

`sell/PROGRESS.md` is the dated log for the whole product. Every unit of work
gets an entry: what shipped, why it was built that way, how it works. Bugs are
recorded with the **symptom**, because the symptom is what a future session
recognises.

## Commands

```bash
python3 build.py              # book → dist/book/index.html (--check validates only)
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
- **No backend, no auth, no database until someone pays.** A login between a
  visitor and the payment link costs conversions and answers nothing.
- **Never publish work as an Artifact.** The claude.ai account is shared, so
  anything published lands in a gallery other people browse. To show something
  visual, serve it locally: `python3 -m http.server` in the right directory.
- Learning styles do not replicate (Pashler 2008). Every format decision is
  justified by **output mode matching the interview**, never by a claim about
  how someone prefers to take information in.
