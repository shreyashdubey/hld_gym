/**
 * Builds preview-NN.html for every reel, plus index.html.
 *
 * Why these exist: an mp4 depends on the viewer's decoder, and VLC on Linux
 * renders these portrait files as a black rectangle with hardware decoding on.
 * A scene is already a pure function of t, so a page can just *play* it — no
 * codec, no container, nothing to fall over. It also scrubs, which reviewing a
 * slow beat actually needs.
 *
 * Generated, never hand-edited: the scene files stay the single source of truth
 * for geometry, timing and beats. Every extraction asserts, so a rename fails
 * loudly here instead of quietly shipping a stale copy.
 *
 *   node preview.mjs
 */
import { readFile, writeFile, readdir } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const FONTS = path.join(HERE, "../src/fonts");

const cut = (src, after, before, what) => {
  const a = src.indexOf(after);
  if (a === -1) throw new Error(`preview.mjs: could not find ${what} start (${after})`);
  const rest = src.slice(a + after.length);
  const b = rest.indexOf(before);
  if (b === -1) throw new Error(`preview.mjs: could not find ${what} end (${before})`);
  return rest.slice(0, b);
};

/* ---- shared stylesheet: inlined once, reused by every page ---- */
let sheet = await readFile(path.join(HERE, "reel.css"), "utf8");
for (const file of ["Archivo-normal-300_700", "Literata-normal-200_900",
                    "IBMPlexMono-normal-400", "IBMPlexMono-normal-600"]) {
  const url = `../src/fonts/${file}.woff2`;
  if (!sheet.includes(url)) throw new Error(`preview.mjs: ${file} not referenced in reel.css`);
  const b64 = (await readFile(path.join(FONTS, `${file}.woff2`))).toString("base64");
  sheet = sheet.replace(url, `data:font/woff2;base64,${b64}`);
}
// Rehome the reel from <body> into a fixed-size stage so the page around it can
// be a normal document, and scope the palettes to the stage so they never fight
// the page's own theme — which also lets both cuts sit on one page.
const bodyRule = "body { width:540px; height:960px; overflow:hidden; background:var(--paper); color:var(--ink); }";
if (!sheet.includes(bodyRule)) throw new Error("preview.mjs: the reel's body rule changed shape");
sheet = sheet
  .replace(bodyRule, ".reel { position:relative; width:540px; height:960px; " +
                     "overflow:hidden; background:var(--paper); color:var(--ink); }")
  .replace(':root[data-theme="dark"] {', ".reel, .reel[data-cut='dark'] {")
  .replace(':root[data-theme="paper"] {', ".reel[data-cut='paper'] {")
  .replace(':root[data-theme="manim"] {', ".reel[data-cut='manim'] {");

const lib = await readFile(path.join(HERE, "reel.js"), "utf8");

const CHROME = `
:root {
  --bg:#ffffff; --surface:#f4f4f4; --fg:#0a0a0a; --fg-2:#4a4a4a; --fg-3:#6b6b6b;
  --rule:#d6d6d6; --rule-strong:#8a8a8a; --hot:#ff5c00; --on-hot:#0a0a0a;
}
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --bg:#0d0d0d; --surface:#161616; --fg:#f0eeec; --fg-2:#b0aca8; --fg-3:#949494;
    --rule:#2e2e2e; --rule-strong:#666666; --hot:#ff6a14; --on-hot:#0a0a0a;
  }
}
:root[data-theme="dark"] {
  --bg:#0d0d0d; --surface:#161616; --fg:#f0eeec; --fg-2:#b0aca8; --fg-3:#949494;
  --rule:#2e2e2e; --rule-strong:#666666; --hot:#ff6a14; --on-hot:#0a0a0a;
}
*, *::before, *::after { box-sizing:border-box; }
body { margin:0; background:var(--bg); color:var(--fg);
  font-family:Archivo, system-ui, sans-serif;
  display:flex; flex-direction:column; align-items:center; gap:20px;
  padding:28px 20px 56px; }
.head { width:100%; max-width:660px; display:flex; flex-direction:column; gap:6px; }
.eb { font-family:'IBM Plex Mono', monospace; font-size:12px; font-weight:600;
      letter-spacing:.14em; color:var(--hot); }
h1 { margin:0; font-size:21px; font-weight:600; letter-spacing:-.01em; }
.sub { margin:0; font-size:14px; line-height:1.5; color:var(--fg-2); max-width:64ch; }
.sub code, .note code { font-family:'IBM Plex Mono', monospace; font-size:12.5px; color:var(--fg); }
a { color:var(--hot); }
.nav { width:100%; max-width:660px; display:flex; flex-wrap:wrap; gap:8px;
       border-bottom:1px solid var(--rule); padding-bottom:16px; }
.nav a { font-family:'IBM Plex Mono', monospace; font-size:12px; text-decoration:none;
         color:var(--fg-2); border:1px solid var(--rule-strong); padding:7px 10px; }
.nav a:hover { border-color:var(--fg); color:var(--fg); }
.nav a[aria-current] { border-color:var(--hot); color:var(--fg); }
/* content-box, deliberately: the global border-box would shrink the content
   area by the 1px rule and let the stage paint over its own edges. */
.frame { box-sizing:content-box; border:1px solid var(--rule-strong); line-height:0;
         height:calc(960px * var(--fit, 1)); width:calc(540px * var(--fit, 1)); }
.reel { transform:scale(var(--fit, 1)); transform-origin:top left; }
.transport { width:min(660px, 100%); display:flex; flex-direction:column; gap:12px; }
.row { display:flex; align-items:center; gap:12px; }
button { font:600 13px/1 Archivo, sans-serif; letter-spacing:.02em;
  background:var(--surface); color:var(--fg); border:1px solid var(--rule-strong);
  border-radius:0; padding:9px 14px; cursor:pointer; white-space:nowrap; }
button:hover { border-color:var(--fg); }
button:focus-visible { outline:2px solid var(--hot); outline-offset:2px; }
#play { background:var(--hot); color:var(--on-hot); border-color:var(--hot); min-width:82px; }
.chips { display:flex; flex-wrap:wrap; gap:6px; }
.chip { font-family:'IBM Plex Mono', monospace; font-weight:400; font-size:11.5px;
        padding:6px 9px; color:var(--fg-2); }
.chip[aria-current="true"] { border-color:var(--hot); color:var(--fg); }
input[type=range] { flex:1; accent-color:var(--hot); height:22px; }
.time { font-family:'IBM Plex Mono', monospace; font-size:13px;
        font-variant-numeric:tabular-nums; color:var(--fg-2); min-width:88px; text-align:right; }
.note { width:100%; max-width:660px; font-size:13px; line-height:1.6; color:var(--fg-3);
        border-top:1px solid var(--rule); padding-top:14px; }
.note b { color:var(--fg-2); font-weight:600; }
`;

const REELS = [
  { id: "01", kernel: "A lock is a statement about the past.", topic: "p2c03 · fencing",
    story: "a hotel keycard",
    crux: "there is no wire between the front desk and the door" },
  { id: "02", kernel: "The read set and the write set must overlap.", topic: "p1c10 · quorums",
    story: "three flatmates and a moved dinner",
    crux: "the two sets overlap, and the overlap is a person" },
  { id: "03", kernel: "Queueing is refusing slowly.", topic: "p2c07 · backpressure",
    story: "a coffee counter in a rush",
    crux: "the cup being made belongs to someone who already left" },
  { id: "04", kernel: "The cache is a suggestion.", topic: "p1c06 · caching",
    story: "sticky notes and a filing cabinet",
    crux: "losing the desk is a slowdown for three notes and data loss for the fourth" },
];

const nav = (current) =>
  `<nav class="nav"><a href="index.html">all reels</a>` +
  REELS.map((r) => `<a href="preview-${r.id}.html"${r.id === current ? ' aria-current="page"' : ""}>` +
                   `reel ${r.id} · ${r.story}</a>`).join("") + `</nav>`;

for (const reel of REELS) {
  const html = await readFile(path.join(HERE, `reel${reel.id}.html`), "utf8");
  const markup = cut(html, "<body>", '<script src="reel.js">', "markup").trim();
  const scene = cut(html, '<script>\n"use strict";', "</script>", "timeline");
  // reel.js autoplays on its own clock in a normal browser; this page owns the
  // clock, so it opts out before the library loads.
  const js = `window.REEL_NO_AUTOPLAY = true;\n${lib}\n${scene}`;

  // charset first, and in the first bytes: without it the browser falls back to
  // a legacy encoding and every middle dot in the captions renders as "Â·".
  // The scene files declare it themselves; these generated pages must too.
  const page = `<meta charset="utf-8">
<title>Reel ${reel.id} — ${reel.story}</title>
<style>${CHROME}
/* ---- the reel's own stylesheet ---- */
${sheet}
</style>

<div class="head">
  <div class="eb">reel ${reel.id} · kernel ${reel.topic}</div>
  <h1>${reel.kernel}</h1>
  <p class="sub">Told as <b>${reel.story}</b>, then relabelled as your system in the last
  two seconds. The crux is one image: ${reel.crux}. Played live rather than decoded, so
  nothing here depends on a codec.</p>
</div>
${nav(reel.id)}

<div class="frame"><div class="reel" id="reel" data-cut="dark">${markup}</div></div>

<div class="transport">
  <div class="row">
    <button id="play" aria-label="Play or pause">Play</button>
    <input type="range" id="scrub" min="0" max="0" step="1" value="0" aria-label="Timeline position">
    <span class="time" id="time">0.0s</span>
  </div>
  <div class="row">
    <div class="chips" id="chips"></div>
    <button id="cut" style="margin-left:auto">Manim cut</button>
  </div>
</div>

<p class="note"><b>Space</b> plays and pauses · <b>&larr; &rarr;</b> step one frame,
with <b>Shift</b> one second · beat buttons jump. The mp4s are in this folder;
if they run in a browser but not in VLC, turn off hardware decoding under
Tools &rarr; Preferences &rarr; Input/Codecs, or use <code>mpv</code>.</p>

<script>
"use strict";
${js}

/* ---- transport ---- */
const reel = document.getElementById("reel");
const scrub = document.getElementById("scrub");
const playBtn = document.getElementById("play");
const timeEl = document.getElementById("time");
const chipsEl = document.getElementById("chips");
let t = 0, playing = false, last = 0;

function fit() {
  // Leave room for the header, nav and transport; never scale past 1:1.
  const f = Math.min(1, (window.innerHeight - 380) / 960, (window.innerWidth - 48) / 540);
  document.documentElement.style.setProperty("--fit", Math.max(0.3, f).toFixed(4));
}
addEventListener("resize", fit);
fit();

function show(ms) {
  t = Math.max(0, Math.min(T_TOTAL, ms));
  window.seek(t);
  scrub.value = Math.round(t);
  timeEl.textContent = (t / 1000).toFixed(1) + "s / " + (T_TOTAL / 1000).toFixed(0) + "s";
  let current = null;
  for (const [at] of BEATS) if (t >= at) current = at;
  for (const el of chipsEl.children)
    el.setAttribute("aria-current", String(Number(el.dataset.at) === current));
}

scrub.max = String(T_TOTAL);
for (const [at, name] of BEATS) {
  const b = document.createElement("button");
  b.className = "chip";
  b.dataset.at = at;
  b.textContent = name;
  b.addEventListener("click", () => { pause(); show(at); });
  chipsEl.append(b);
}

function frame(now) {
  if (!playing) return;
  if (last) show(Math.min(t + (now - last), T_TOTAL));
  last = now;
  if (t >= T_TOTAL) { pause(); return; }
  requestAnimationFrame(frame);
}
function play() {
  if (t >= T_TOTAL) t = 0;
  playing = true; last = 0; playBtn.textContent = "Pause";
  requestAnimationFrame(frame);
}
function pause() { playing = false; playBtn.textContent = "Play"; }

playBtn.addEventListener("click", () => (playing ? pause() : play()));
scrub.addEventListener("input", () => { pause(); show(Number(scrub.value)); });
/* Three cuts, cycled. The button names the one you get next, not the one you
   are looking at — a button labelled with the current state reads as a status. */
const CUTS = ["dark", "paper", "manim"];
const cutBtn = document.getElementById("cut");
function setCut(name) {
  reel.dataset.cut = name;
  const next = CUTS[(CUTS.indexOf(name) + 1) % CUTS.length];
  cutBtn.textContent = next[0].toUpperCase() + next.slice(1) + " cut";
}
cutBtn.addEventListener("click", () =>
  setCut(CUTS[(CUTS.indexOf(reel.dataset.cut) + 1) % CUTS.length]));
setCut("dark");
addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT") return;
  if (e.key === " ") { e.preventDefault(); playing ? pause() : play(); }
  if (e.key === "ArrowRight") { pause(); show(t + (e.shiftKey ? 1000 : 1000 / 60)); }
  if (e.key === "ArrowLeft") { pause(); show(t - (e.shiftKey ? 1000 : 1000 / 60)); }
});

document.fonts.ready.then(() => show(0));
show(0);
</script>
`;
  await writeFile(path.join(HERE, `preview-${reel.id}.html`), page);
}

/* ---- index: every reel on one screen ---- */
const files = await readdir(HERE);
const index = `<meta charset="utf-8">
<title>Kernel Reels</title>
<style>${CHROME}
.grid { width:100%; max-width:660px; display:flex; flex-direction:column; gap:0; }
.card { display:grid; grid-template-columns:56px 1fr; gap:18px;
        border-top:1px solid var(--rule); padding:20px 0; text-decoration:none; color:inherit; }
.card:last-child { border-bottom:1px solid var(--rule); }
.card:hover .kn { color:var(--hot); }
.num { font-family:'IBM Plex Mono', monospace; font-size:12px; font-weight:600;
       color:var(--fg-3); letter-spacing:.1em; padding-top:4px; }
.kn { font:600 19px/1.3 Literata, serif; letter-spacing:-.01em; }
.meta { font-family:'IBM Plex Mono', monospace; font-size:12px; color:var(--fg-3); margin-top:8px; }
.cx { font-size:13.5px; line-height:1.55; color:var(--fg-2); margin-top:8px; }
</style>

<div class="head">
  <div class="eb">hld gym · kernel reels</div>
  <h1>Four kernels, four everyday scenes</h1>
  <p class="sub">Each reel opens on something ordinary going wrong, then relabels the same
  picture as your system in the last two seconds. 45 seconds, 1080&times;1920, silent with
  burned captions. Every one carries a single crux image it exists to deliver.</p>
</div>

<div class="grid">
${REELS.map((r) => `  <a class="card" href="preview-${r.id}.html">
    <div class="num">REEL<br>${r.id}</div>
    <div>
      <div class="kn">${r.kernel}</div>
      <div class="cx">Told as ${r.story}. The crux: ${r.crux}.</div>
      <div class="meta">${r.topic}${files.includes(`reel${r.id}-dark.mp4`) ? " · mp4 rendered" : " · not yet rendered"}</div>
    </div>
  </a>`).join("\n")}
</div>

<p class="note">Play them in the browser rather than a desktop player: these are portrait
h264, and VLC on Linux shows them black when hardware decoding is on. The pages animate
the scene directly, so no decoder is involved at all.</p>
`;
await writeFile(path.join(HERE, "index.html"), index);
console.log(`index.html + ${REELS.length} preview pages (${(sheet.length / 1024).toFixed(0)}kB of inlined fonts each)`);
