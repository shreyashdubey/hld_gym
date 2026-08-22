# The Origins portrait system

51 person-cards. ~10 agents who cannot see each other's work. The only way that
ends as one book instead of a scrapbook is if the drawing is not a drawing
decision. What follows is a fixed plate with five closed slots. An agent picks
values from a list and pastes strings in a fixed order. It never composes.

Reference plates, drawn with this system and nothing else:
`src/assets/ref-a.svg`, `src/assets/ref-b.svg`, `src/assets/ref-c.svg`.

---

## 0. Three facts that decide everything

**A portrait ships as `<img>`, so it is an isolated document.** `app.js` builds
card art with `document.createElement('img')` and `setAttribute('src', card.asset)`.
An SVG referenced from `<img>` gets no page CSS, no page fonts, no external
resources, no script. Three consequences, all load-bearing:

- **`dg-node`, `dg-edge`, `dg-txt`, `dg-bad`, `dg-good`, `dg-zone` do not work here.**
  The 197 inline diagrams live in the page and inherit `src/style.css`. A portrait
  does not. Using those class names produces black-on-black. Every portrait carries
  its own four-line `<style>`, given below, byte for byte identical.
- **No `<text>`, ever.** Archivo / Literata / IBM Plex Mono are base64'd into the
  built HTML. They are unreachable from the image document, so any `<text>` renders
  in whatever the machine's default sans happens to be — different on every reader's
  screen, and foreign to the book on all of them. Words belong in HTML.
- **No `role`, no `<title>`.** `app.js` sets `img.alt = card.title`, which is the
  accessible name. Anything inside is dead weight.

**The theme system is a filter, not a palette.** `.card-art` is
`filter: grayscale(1) contrast(1.25)` plus `mix-blend-mode: luminosity`; the three
dark themes swap in `contrast(1.15) invert(1)`. So the file must be authored in
exactly **two greys on an opaque plate** — ink `#000`, ground `#EEE` — and the
themes then happen for free: near-black on near-white in paper, near-white on
near-black in the other three, hue and saturation lifted off `--panel` (neutral in
paper and dark, faintly blue in manim, green on the phosphor tube). Do not add a
third tone. Do not add colour. Do not assume a polarity — every shape has to read
both ways round, which is why the drawing is a line drawing and not a tonal one.

**The legal floor.** Nothing here is traced from or derived from any photograph.
Everything below is authored geometry, and the same twenty-one path strings are
reused across all 51 plates, which is the point: a mark assembled from a fixed
public vocabulary cannot be a derivative work of anyone's photograph, because it
was not made from one. No organisation marks at all — see §7.

---

## 1. The plate

`viewBox="0 0 96 120"` — a 4:5 portrait plate, one user unit ≈ 1.5 CSS px at the
`max-width: 9rem` the card gives it.

The vertical grid, fixed for all 51:

| y | what |
|---|---|
| 1 / 119 | plate frame |
| 25 | crown of head |
| 33–41 | hairline band (where every `hair` value terminates) |
| 46 | eye line |
| 50 | cx 48 — centre of head; nose starts |
| 57 | nose base |
| 68–92 | neck |
| 75 | chin |
| 88 | shoulder line |
| 90–104 | collar |

Head is `cx=48 cy=50 rx=21 ry=25`. Everything else hangs off that ellipse.

### The file, verbatim

Copy this whole thing. The first three lines never change. `⟨…⟩` are the slots.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 120"><style>.p{fill:#EEE}.g{fill:url(#h)}.l{fill:none}.p,.g,.l{stroke:#000;stroke-width:1.4}</style><pattern id="h" width="4" height="4" patternUnits="userSpaceOnUse"><path d="M1 1h2v2H1z"/></pattern><path class="p" d="M1 1h94v118H1zM40 92V68h16v24"/><path class="g" d="M1 121c3-23 22-33 47-33s44 10 47 33z"/>⟨FACIAL·BACK⟩⟨HAIR·BACK⟩<ellipse class="p" cx="48" cy="50" rx="21" ry="25"/>⟨HAIR·FRONT⟩⟨FACIAL·FRONT⟩<circle cx="39" cy="46" r="2"/><circle cx="57" cy="46" r="2"/><path class="l" d="M48 50v6h4"/>⟨EYEWEAR⟩⟨COLLAR⟩</svg>
```

The four classes, and the fifth case:

| class | means | used by |
|---|---|---|
| `.p` | opaque light ground + ink hairline | plate, neck, head |
| `.g` | halftone + ink hairline | shoulders, `stubble` |
| `.l` | stroke only, no fill | nose, eyewear, collar V |
| *(none)* | solid ink, no stroke | hair, beard, eyes, tie knot |

The fifth case is not an oversight. Black fill and no stroke are the SVG defaults,
so an ink mass is the cheapest possible element: `<path d="…"/>`. If you find
yourself writing `fill="#000"`, delete it.

### Why these four elements and no others

- **Plate + neck are one path.** The frame is the ground *and* the boundary — one
  `<path>` doing both jobs, and the neck rides in the same subpath because it is
  the same class and sits at the same depth. The frame is the single strongest
  unifier in the set: 51 plates of identical outer geometry read as a series before
  the reader has looked at any face.
- **The halftone is the house texture.** A 4-unit tile with a 2×2 ink dot, 25%
  coverage. I tried a flat mid-grey shoulder instead and it read as clip-art
  avatar; the halftone reads as a printed plate, which is exactly what
  `style.css` promises ("so a press photo and an authored portrait read as one
  sketchbook"). The pattern tile needs no light backing — the plate underneath is
  already `#EEE`, so the gaps are ground.
- **The face is two eye pips and one nose tick, and that is the entire fixed
  face.** No mouth, no brow, no ears. See §4.

### Slot order is the drawing order

`FACIAL·BACK → HAIR·BACK → head → HAIR·FRONT → FACIAL·FRONT → eyes → nose → eyewear → collar`

The two "back" points are before the head, so the head's opaque `#EEE` fill cuts
the face out of whatever is behind it. That is how long hair and beards work
without any path having to trace around the face. Never reorder.

---

## 2. The vocabulary

Closed. Pick a listed value or pick `none`. Do not interpolate, do not scale, do
not mirror, do not invent a sixth hair.

### hair — 6 values

| value | back | front |
|---|---|---|
| `none` | — | — |
| `crop` | — | `<path d="M30 37A21 25 0 0 1 66 37Q48 41 30 37Z"/>` |
| `recede` | — | `<path d="M33 33A21 25 0 0 1 63 33Q48 39 33 33Z"/>` |
| `full` | `<path d="M24 46a24 28 0 0 1 48 0v28H24Z"/>` | — |
| `volume` | `<path d="M20 44a28 28 0 1 1 56 0 28 28 0 1 1-56 0"/>` | — |
| `tied` | — | `<path d="M30 37A21 25 0 0 1 66 37Q48 41 30 37ZM61 32a7 7 0 1 0 14 0 7 7 0 1 0-14 0"/>` |

`crop` and `recede` are caps that terminate on the head ellipse — they are the
hairline, not a hairstyle. `full` and `volume` are masses behind the head; the
head punches the face out. `tied` is `crop` plus a bun.

**`hair` is the one slot where `none` is a positive claim.** It means documented
bald or shaved. If a subject's hair is simply undocumented, use `crop`.

### facial — 5 values

| value | back | front |
|---|---|---|
| `none` | — | — |
| `beard` | `<ellipse cx="48" cy="56" rx="24" ry="26"/>` | — |
| `stubble` | `<ellipse class="g" cx="48" cy="56" rx="24" ry="26"/>` | — |
| `goatee` | `<ellipse cx="48" cy="64" rx="13" ry="19"/>` | — |
| `moustache` | — | `<path d="M36 56q12-4 24 0-2 5-12 5t-12-5Z"/>` |

The rule that makes these work: **facial hair changes the silhouette, it does not
sit on the face.** A beard is an ellipse *behind* the head, wider and lower than
the head, so what you see is jaw and chin growing outside the head outline. This
was the hardest thing in the system to get right and the reason is worth knowing:
in a two-tone face, ink means *feature* and light means *skin*, so any ink mass
painted inside the face outline gets read as a mouth. A flat-topped one reads as a
bandit mask; a curved one reads as a grin. Neither is fixable by nudging the
curve. Only moving the mass outside the silhouette fixes it. `moustache` is the
single exception, allowed in front because it is small and anchored under the
nose tick, and it tested clean.

`beard` and `stubble` are the same ellipse in ink and in halftone.

### eyewear — 4 values

| value | markup |
|---|---|
| `none` | — |
| `round` | `<path class="l" d="M44 46h8M29 45h5m28 0h5M34 46a5 5 0 1 0 10 0 5 5 0 1 0-10 0m18 0a5 5 0 1 0 10 0 5 5 0 1 0-10 0"/>` |
| `rect` | `<path class="l" d="M34 42h11v8H34zm17 0h11v8H51zm-6 4h6M29 43l5 1m28 0 5-1"/>` |
| `heavy` | `<path class="l" stroke-width="2.8" d="M34 42h11v8H34zm17 0h11v8H51zm-6 4h6M29 43l5 1m28 0 5-1"/>` |

`heavy` is `rect` at double weight — the 1960s heavy frame — and being the same
path guarantees it can never drift into a different pair of glasses. The temple
ticks are not optional: without them the lenses float and read as goggles.

### collar — 2 values

| value | markup |
|---|---|
| `open` | `<path class="l" d="M40 90l8 12 8-12"/>` |
| `tie` | `<path class="l" d="M40 90l8 12 8-12"/><path d="M48 100l4 4-4 14-4-14z"/>` |

There is no `collar-none`. A bare halftone dome looked unfinished next to its
neighbours in the deck grid, and no card is served by it. `open` is the default;
`tie` when the source shows formal business or official dress.

### The slots I enumerated and then cut

**Headwear.** I drew a cap, tested it, and removed the slot. Scanning the cast for
subjects a hat would actually serve: John Owen the 1921 Cambrian Railways
passed-fireman, and Craig Faust in the TMI-2 control room, who wore no hat.
One card. Meanwhile the value read as a bowler and the slot's real effect would
have been to invite ten agents to decide independently who looks like they wore
something. A slot that exists "just in case" is a drift vector. Cut.

**Ears.** Hidden by every hair value except `none`, and at `none` they added
nothing. Cut.

**A side-parted hair value.** `crop` already covers it, and two near-identical
short-hair values is exactly how a vocabulary starts leaking. Cut.

### The size of the space

6 × 5 × 4 × 2 = **240 distinct plates** for 51 subjects. That is deliberately not
huge. If the sources say nothing about a feature, use the default — do not invent
variety to dodge a repeat. Two subjects landing on the same mark is fine and
expected: the card already carries `title` and `sub`, and the portrait was never
the identifying element. Inventing a beard to make a plate unique is a claim about
a person's face that no source supports, which is both dishonest and the one thing
this system exists to prevent.

---

## 3. The budget

**Under 900 bytes, and the grammar cannot express anything larger.**

Measured over all 240 legal combinations:

| | bytes |
|---|---|
| fixed skeleton (preamble + plate + bust + head + eyes + nose) | 518 |
| minimum plate (`none`/`none`/`none`/`open`) | 556 |
| median | 735 |
| **maximum** (`tied` + `stubble` + `round` + `tie`) | **843** |
| no-known-likeness mark | 483 |
| group mark | 461 |

That maximum is a property of the closed vocabulary, not a target anyone has to
watch. 51 plates at the median is ~37 KB of siblings to a built HTML file — the
assets never enter the HTML at all, so the 403 KB gzip headroom is untouched.

The check, which is the whole check:

```sh
# over budget, or not a single line
awk 'length($0) > 900 || FNR > 1 {print FILENAME": too big or multi-line"}' src/assets/pt-*.svg
# anything that cannot ship. The sed strips the one legal http:// in the file.
for f in src/assets/pt-*.svg; do
  sed 's|xmlns="http://www.w3.org/2000/svg"||' "$f" |
    grep -qE 'https?://|<text|dg-[a-z]|role=|<title|fill="#000"' && echo "$f: forbidden token"
done
```

Both should print nothing. Note the `sed`: `xmlns="http://www.w3.org/2000/svg"` is
mandatory in a standalone SVG and is the one `http://` allowed anywhere near this
book. It is not a violation of `build.py`'s external-URL ban — that ban runs over
chapter and origin *HTML fragments* (`validate_html`), and an asset's bytes are
never read by the build, only `shutil.copytree`'d. Do not "fix" the xmlns.

One line per file is part of the spec: these are generated-shaped artefacts, and a
one-line diff is a diff you can actually read.

---

## 4. How abstract, and why

**Two eye pips, one nose tick. No mouth, no brow, no ears, no jaw shading, no
cheek, no shoulders-of-a-particular-suit.** Everything that varies between the 51
lives in four slots that describe *category* — hair mass, facial-hair mass,
eyewear shape, collar — and never proportion. Every head in the book is the same
ellipse at the same size in the same place.

This is not minimalism for taste. It is doing three jobs at once.

**Legal.** An abstract mark assembled from a shared public vocabulary is not a
derivative of any photograph, and cannot become one, because it was not made from
one. There is no step in this process at which an agent has a photo open. The
question "is this plate a copy of that press photo of Pat Selinger" has an answer
that survives inspection: the plate's every path string also appears in six other
chapters' plates. Nothing about it is *of* her.

**Honest.** Photographic evidence for this cast is wildly uneven. There are many
good photographs of Max Levchin and Brad Fitzpatrick, one or two known images of
J. S. Liptay, and, as far as the record goes, nothing at all for the Terremark
duty manager on 26 September 2013 or for "Chuanhui". A likeness-seeking system
makes that unevenness visible as quality: sharp portraits for the famous, mush for
everyone else, which quietly tells the reader that the Bellcore standards editor
mattered less. A mark-based system flattens it. Every subject gets the same
attention because every subject gets the same ellipse.

**Consistent under parallelism.** The failure mode is not that one agent draws
badly. It is that ten agents each draw *well*, in ten different hands. Removing
the mouth removes expression; removing expression removes the largest surface an
agent has to be individually good on. What is left is a lookup.

The nose tick is the one place I spent a shape on nothing but legibility, and it
earns it: without it the face is two dots in a blank oval, glasses have nothing to
sit on, and — as §2 records — a moustache reads as a mouth. It is identical in all
51, so it costs no drift.

---

## 5. The no-known-likeness mark

For The Terremark manager (p1c04-c2), and for anyone whose appearance is genuinely
undocumented — on this cast that is likely to include Chuanhui, CCP Veritas,
G. Ratta, F. G. Foster and John Owen.

`src/assets/ref-c.svg` is the mark. One fixed file, referenced by every card that
needs it; copy it to `src/assets/pt-unknown.svg` and point the cards at that. Never
author a variant.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 120"><style>.p{fill:#EEE}.g{fill:url(#h)}.l{fill:none}.p,.g,.l{stroke:#000;stroke-width:1.4}</style><pattern id="h" width="4" height="4" patternUnits="userSpaceOnUse"><path d="M1 1h2v2H1z"/></pattern><path class="p" d="M1 1h94v118H1zM40 92V68h16v24"/><path class="g" d="M1 121c3-23 22-33 47-33s44 10 47 33z"/><ellipse class="p" stroke-dasharray="3" cx="48" cy="50" rx="21" ry="25"/><path class="l" d="M40 90l8 12 8-12"/></svg>
```

**Same plate. Same shoulders, solid and in the same halftone, with the same
collar. Same head, in the same place, at the same size — drawn as a dashed
hairline, and empty.**

It reads as a decision rather than a gap for three reasons.

- The dash is not invented for this. `style.css` already uses `stroke-dasharray`
  for `.dg-zone` — "a boundary that is notional, not a thing" — across 197
  diagrams. The mark speaks the book's existing grammar; a reader who has met a
  dashed boundary elsewhere in the book reads this one correctly on sight.
- **The body is solid and the head is not.** That is the actual claim, and it is
  true: this person existed, held a post, and did the thing the chapter is about.
  What is unrecorded is their face. A blank plate or a question mark would say
  "we could not be bothered". A solid halftone bust under a dashed head says
  "the record has shoulders and no face", which is precisely the situation.
- Nothing is missing that the other plates have *except the four slot values*.
  There is no placeholder grey, no icon, no `?`. It is the same drawing with the
  variable part withheld.

Use it when the record is silent. Do not use it because a search was hard —
the honest signal only stays honest if it is rare and true.

---

## 6. The group mark

Seven of the 51 person-cards name more than one human: `p2c04-c1` (Imine, Molli,
Oster and Rusinowitch), `p3c02-c1` (Grover, King and Kushler), `p3c24-c1` (Weber,
Schek and Blott), `p3c08-c1`, `p3c12-c1`, `p3c15-c1`, `p3c17-c1`. Fourteen percent
of the deck. The plate holds one bust, so this needs an answer rather than a
convention.

Drawing the first-named author is arbitrary and slightly dishonest. Drawing two
busts side by side at half scale doubles the shape count and produces two marks
nobody can tell apart anyway — at this abstraction "Molli" and "Oster" are the
same ellipse, so a two-up plate conveys a headcount and nothing else. So: one
fixed file, `src/assets/pt-group.svg`, for all seven.

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 120"><style>.p{fill:#EEE}.g{fill:url(#h)}.l{fill:none}.p,.g,.l{stroke:#000;stroke-width:1.4}</style><pattern id="h" width="4" height="4" patternUnits="userSpaceOnUse"><path d="M1 1h2v2H1z"/></pattern><path class="p" d="M1 1h94v118H1z"/><path class="g" d="M1 121c3-23 22-33 47-33s44 10 47 33z"/><ellipse class="p" cx="34" cy="60" rx="17" ry="21"/><ellipse class="p" cx="62" cy="60" rx="17" ry="21"/></svg>
```

Two overlapping heads, no features, sharing one shoulder mass; no neck and no
collar, because there is no single body. Solid outlines, not dashed — these people
are documented, they are simply not being portrayed individually. Two heads is a
mark, not a census: it means "a team", and it is the same file whether the card
names two people or four.

---

## 7. Organisations get no mark at all

Not authored geometry, not a monogram, not initials in a box. Nothing.

**The lawsuit risk runs the wrong way.** *Toyota v. Tabari* draws the line at the
stylised mark, and the word is safe. An authored geometric stand-in for IBM, Xerox
PARC or the Federal Reserve is not the word — it is a mark, made by us, doing the
job of theirs. Worse, it is a brief that instructs ten agents to invent something
evocative of a company, which is a request to approximate a logo while calling it
geometry. A closed vocabulary cannot defend against that, because the drift is
semantic, not geometric: any two agents can draw the same eight-bar shape and only
one of them meant IBM.

**Even setting the name in type is not available here.** §0: an `<img>`-referenced
SVG cannot reach the book's fonts, so "Bellcore" set in an asset would arrive in
whatever the reader's machine calls a default sans. There is no way to put type in
one of these files and have it be the book's type.

**And it is already solved.** Every person-card's `sub` field carries the
organisation — `"1979 · IBM San Jose Research Laboratory"`, `"1994 · Bellcore ·
chief editor, ATM Forum UNI 3.1"` — and `app.js` renders it into `.card-sub` as
HTML text. That is the org mark: real Archivo, real `--ink-2`, correct in all four
themes, selectable, searchable, screen-readable, and zero bytes of new asset.
Rung one of the ladder: this does not need to exist.

If a future artifact-suit card genuinely needs an organisation to be *pictured*,
the answer is a diagram in the chapter body, inline, using `dg-*` like the other
197 — not an asset.

---

## 8. Procedure for an agent drawing one plate

1. Read the card's `title`, `sub`, `year`, and the chapter's `cite.json`. Note only
   what a source actually states about appearance.
2. Multi-person card → point `asset` at `assets/pt-group.svg`. Stop.
   Appearance genuinely unrecorded → `assets/pt-unknown.svg`. Stop.
3. Otherwise pick one value per slot. Undocumented feature → `crop` for hair,
   `none` for facial and eyewear, `open` for collar. Never invent.
4. Paste the template from §1, substitute the five slots, delete the `⟨⟩` markers.
   One line, no newline inside the file.
5. Save as `src/assets/pt-<card-id>.svg` (e.g. `pt-p1c03-c1.svg`) and set the
   card's `"asset": "assets/pt-p1c03-c1.svg"`.
6. Run the two checks in §3, then `python3 build.py --check`.

Forbidden, and each of these has bitten something already: any `https?://`;
`<text>`; `dg-*` class names; a third grey; any colour; `transform`; `opacity`;
`stroke-linecap` / `stroke-linejoin`; a path not listed in §2; changing the
`viewBox`, the head ellipse, the eye positions or the nose; adding an element the
template does not have.

---

## 9. The three references, and what looking at them changed

- `ref-a.svg` — 797 B — `recede` + `beard` + `round` + `tie`
- `ref-b.svg` — 598 B — `full` + `none` + `none` + `open`
- `ref-c.svg` — 483 B — the no-known-likeness mark

Rendered side by side, in a real `.card` at `max-width: 9rem`, in all four themes,
with the real filter chain. Five things changed *because* of that and not before:

1. **The beard was rebuilt twice.** As a flat-topped ink mass across the lower
   face it read as a bandit mask; curved, it read as a wide grin; with the
   moustache merged in, still a grin. All three are the same failure — ink inside
   the face outline is a feature, not hair. It only became a beard when it moved
   *behind* the head and started changing the silhouette. §2 now states that as a
   rule, because it is not obvious and every agent adding facial hair will hit it.
2. **A nose tick was added to the fixed skeleton.** Two dots in a blank oval had no
   vertical structure, which is what let every facial-hair shape read as a mouth.
   Fixed, so it costs no variance.
3. **A flat mid-grey shoulder was tried and rejected** in favour of the halftone.
   Side by side, flat read as clip-art and halftone read as print. It costs 109 of
   the 843 bytes and it is the single loudest "same hand" signal in the set.
4. **The vocabulary got tighter, not looser.** Headwear cut entirely; a
   side-parted hair value cut as a near-duplicate of `crop`; `collar-none` cut
   because a bare dome looked unfinished in the grid; `heavy` eyewear redefined as
   `rect` at 2.8 stroke rather than its own path, so the two can never diverge.
5. **The group mark exists at all** only because reading the 51 cards turned up
   seven multi-person subjects — a case the brief did not name and the plate
   cannot hold.

`ref-*.svg` are reference plates, not content. Nothing references them, so they
cost nothing but the copy into `dist/origins/assets/`; keep them as the visual
baseline to check a new plate against, or delete them once the 51 land.
