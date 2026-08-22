# The origins figure system

How a real photograph or a company mark gets into a chapter. One contract, so
forty agents produce one book instead of forty.

Read with `STYLE_GUIDE.md` §7 and
`docs/superpowers/specs/2026-08-22-origins-design.md`.

## 1. What this is for

Until now the only images in `/origins` were 51 authored portraits, and they
appeared in one place: the card, after recall. This system puts **real
photographs of the real people and real marks of the real companies inline in
the teaching body**, beside the paragraph that talks about them, so a reader
scrolling the chapter sees the face of the person whose constraint they are
about to learn.

`/book` is unchanged. Figures are stripped from it at build time.

## 2. The markup, exactly

One `<img>` per `<figure>`. No nesting. Both attributes on the figure.

```html
<figure class="fig" data-mode="origins">
  <img src="assets/photo/p2c10-mcilroy.jpg" alt="Doug McIlroy in 2011"
       width="407" height="564" loading="lazy">
  <figcaption>Doug McIlroy, who wrote the pipe into the shell overnight.
    <span class="credit">Photo Denise Panyik-Dale, CC BY 2.0</span></figcaption>
</figure>
```

A company mark is the same shape with one extra class:

```html
<figure class="fig fig-mark" data-mode="origins">
  <img src="assets/mark/google.svg" alt="Google" width="272" height="92" loading="lazy">
  <figcaption>Google's own wordmark, 2015.
    <span class="credit">Google wordmark, public domain (below the threshold of
    originality). Trademark of Google LLC, used nominatively.</span></figcaption>
</figure>
```

Rules the build enforces:

- `data-mode="origins"` is required on the figure and is what strips it from `/book`.
- `src` starts with `assets/`. No `https://` anywhere in a fragment, ever.
- `alt` is non-empty and describes the image, not the licence.
- A `<figcaption>` is required, and it must contain exactly one
  `<span class="credit">`.
- **The credit text must match the manifest's `credit` field byte for byte.**
  That is the whole point of the manifest: the attribution that ships is the
  attribution someone verified.
- No `<figure>` inside a `<figure>`.
- `width` and `height` are the intrinsic pixel size of the file. They stop the
  page reflowing as images arrive.

## 3. Where files live

```
src/assets/photo/<slug>.jpg      real photographs of real people
src/assets/mark/<slug>.svg       company marks
src/assets/<cid>-person.svg      the authored portraits, unchanged
```

Only referenced files ship. A file nobody points at warns and stays out of
`dist/`.

## 4. The manifest

Every file under `photo/` or `mark/` needs a row, or the build fails. Rows live
in `src/assets/*.manifest.json`; build.py reads all of them.

```json
{
  "_comment": "who wrote this, what pass, what it covers",
  "entries": {
    "photo/p2c10-mcilroy.jpg": {
      "kind": "person",
      "subject": "M. Douglas McIlroy",
      "chapters": ["p2c10"],
      "licence": "CC BY 2.0",
      "author": "Denise Panyik-Dale",
      "credit": "Photo Denise Panyik-Dale, CC BY 2.0",
      "source": "https://commons.wikimedia.org/wiki/File:Douglas_McIlroy.jpeg",
      "source_file": "File:Douglas_McIlroy.jpeg",
      "retrieved": "2026-08-22",
      "sha256": "<of the file as shipped>",
      "modifications": "downscaled to 480px on the long edge, EXIF stripped"
    }
  }
}
```

A `mark` row adds `"trademark": "Google LLC"`.

`credit` is the string that appears in the figcaption AND in the credits block.
Write it once, here.

## 5. What may be downloaded — the only rule that carries legal weight

**Read the licence off the file's own description page**, via the Commons API's
`extmetadata` (`LicenseShortName`, `UsageTerms`, `Artist`, `LicenseUrl`), never
off the article that happens to use the file. An earlier pass on this project
found two decoys that way: a CC BY-SA tag applied by an uploader to a photograph
of someone else's copyrighted oil painting, and a `{{PD-China}}` tag with no US
copyright tag at all.

**People — allowed:** CC0, CC BY, CC BY-SA, public domain of any flavour
(PD-US-expired, PD-USGov, PD-self), GODL-India, and other verifiably free
licences. **Not allowed:** anything tagged non-free, fair use,
`{{Non-free biog-pic}}`, "all rights reserved", press-kit-only, or with a
no-derivatives (ND) or non-commercial (NC) term. This is a commercial site.

**Marks — two separate questions, both must pass:**

*Copyright.* A logo is only downloadable if Commons hosts it under a free tag —
`{{PD-textlogo}}`, `{{PD-ineligible}}`, `{{PD-shape}}`, CC0, CC BY. A great many
wordmarks qualify because plain type is below the threshold of originality. A
logo tagged non-free/fair-use on English Wikipedia is **not** reusable; that tag
is Wikipedia's own exemption and does not travel. Do not download those.

*Trademark.* A free copyright status does not make a mark unencumbered — it is
still a trademark. Reproducing it to identify the company the history describes
is nominative use, which is what every newspaper and textbook relies on. Keep it
inside those lines: reproduce the mark **unaltered**, never recolour or restyle
it, never place it near anything that reads as endorsement or partnership, never
use it as this product's own branding, favicon, or OG image, and always name the
owner in the credit.

**Where no free mark exists**, do not improvise one and do not trace it. Write
the company name in the book's own type — that is the fallback, and it is
always available.

## 6. Processing

Fetch and processing scripts may use Pillow. **`build.py` may not** — it takes
no third-party dependency, ever.

- Photographs: downscale so the long edge is 480px, strip EXIF, JPEG quality 82,
  progressive. **Do not crop.** The book's fixed-aspect frame is done in CSS with
  `object-fit`, which costs nothing legally and stays reversible.
- Marks: prefer the SVG. Sanitise it — remove `<script>`, `<foreignObject>`, and
  any external `href`/`xlink:href`. Under 12KB. If only a raster exists, 240px
  wide PNG.
- Record the byte size and sha256 of the file **as shipped**.
- Never modify a mark beyond sanitising and never redraw it.

## 7. Placement in a chapter

A figure earns its place the same way a story does.

- **At most three per chapter**, and most chapters want one or two.
- Put it beside the paragraph that names the person or company, not at the top
  as decoration. If the reader has to scroll to work out who it is, it is in the
  wrong place.
- The figcaption is a sentence of the book, not a label. "Doug McIlroy, who wrote
  the pipe into the shell overnight" teaches; "Doug McIlroy" does not. One
  sentence, then the credit span.
- A person gets a figure in the chapter that tells their story. Do not repeat the
  same face in three chapters.
- A mark goes where a company is an **actor in the history** — where the incident
  happened, who shipped the fix. Not next to every mention of a technology that
  shares a name with a company. Redis is named 213 times in this book and almost
  none of them are about the company.
- Figures go in one of two places, and the difference matters.

  **The teaching body**, `<id>.html`, **below the first `<h2>`.** Anything above
  that heading is deleted by `swapColdOpen`, so a figure there vanishes.

  **The origin story**, `<id>.origin.html`. This is where the company that
  *acted in the history* usually belongs, and the first placement pass could not
  reach it. Nine agents independently reported the same thing: TSB, RBS, Sun,
  Fujitsu, JMA, FirstEnergy, IBM, Xerox, Bell Labs and a dozen others are named
  only in the story, never in the body, so their marks had nowhere to go. In
  `/origins` the story renders at the top of the chapter and is the most-read
  part of it. A mark beside the paragraph describing what that company did is
  the best placement in the book, not a consolation.

  Two rules apply only to story figures. The 260-word cap counts prose with
  figures excluded, so a figure costs no story budget. And a figcaption is
  capped at 20 words excluding its credit — that cap is what stops the
  exclusion becoming a loophole for extra narrative.

  **One figure per story. Two at the absolute most, and only if the story has
  two distinct actors.** The story is 260 words; it cannot carry a gallery.

## 8. Cards

Where a verified photograph of a card's subject exists, the card's `asset`
switches from the authored portrait to the photograph. The portrait file stays in
the repo; it simply stops being referenced and stops shipping. The set is
deliberately mixed — CSS gives photographs the same ink treatment the drawings
get, so they sit together.
