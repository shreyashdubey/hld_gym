/**
 * Shoots each of a reel's named beats and tiles them into one contact sheet.
 *
 * This is the check that matters: "the animation is running" is measurable from
 * the DOM, "the animation is visible" is not. Look at the pixels at a chosen
 * frame before spending minutes on a full render. Every defect worth fixing in
 * reel 01 was found here and none of them were visible from the DOM.
 *
 * Beats come from the scene's own `mount({beats})`, so this script never holds
 * a second copy of a timeline that can drift.
 *
 *   node contact.mjs [--reel 01] [--theme dark|manim]
 */
import { chromium } from "playwright";
import { mkdir, rm } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const arg = (n, d) => { const i = process.argv.indexOf(`--${n}`); return i === -1 ? d : process.argv[i + 1]; };
const REEL = arg("reel", "01");
const THEME = arg("theme", "dark");
const OUT = path.join(HERE, `beats-${REEL}`);

await rm(OUT, { recursive: true, force: true });
await mkdir(OUT, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: 1 });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto("file://" + path.join(HERE, `reel${REEL}.html`));
await page.evaluate((t) => document.documentElement.setAttribute("data-theme", t), THEME);
await page.evaluate(() => document.fonts.ready);

const beats = await page.evaluate(() => window.BEATS);
if (!beats?.length) throw new Error(`reel${REEL}: no beats declared in mount()`);

for (const [t, name] of beats) {
  await page.evaluate((ms) => window.seek(ms), t);
  await page.screenshot({ path: path.join(OUT, `${String(t).padStart(6, "0")}-${name.replace(/\s+/g, "-")}.png`) });
}
await browser.close();

if (errors.length) {
  console.error(`FAIL reel${REEL}: ${errors.length} page error(s)`);
  for (const e of errors) console.error("  " + e);
  process.exit(1);
}

// Tile as close to square as the beat count allows.
const cols = Math.ceil(Math.sqrt(beats.length));
const rows = Math.ceil(beats.length / cols);
await promisify(execFile)("ffmpeg", [
  "-y", "-loglevel", "error",
  "-pattern_type", "glob", "-i", path.join(OUT, "*.png"),
  "-filter_complex", `scale=260:-1,tile=${cols}x${rows}:padding=6:color=0x444444`,
  "-frames:v", "1", path.join(HERE, `contact-${REEL}-${THEME}.png`),
]);
console.log(`contact-${REEL}-${THEME}.png — ${beats.map((b) => b[1]).join(", ")}`);
