/**
 * Shoots a reel scene through headless Chromium, two ways.
 *
 *   node shoot.mjs --beats  [--reel 01] [--theme dark|paper|manim]
 *   node shoot.mjs --frames [--reel 01] [--fps 30] [--scale 2] [--theme dark|paper|manim]
 *
 * --beats shoots each named beat and tiles them into one contact sheet. This is
 * the check that matters: "the animation is running" is measurable from the
 * DOM, "the animation is visible" is not. Look at the pixels at a chosen frame
 * before spending minutes on a full render. Every defect worth fixing in reel
 * 01 was found here and none of them were visible from the DOM. Beats come
 * from the scene's own `mount({beats})`, so this script never holds a second
 * copy of a timeline that can drift.
 *
 * --frames writes one PNG per frame for ffmpeg. Deterministic on purpose:
 * Playwright's own recordVideo captures at whatever rate the page happens to
 * paint, so a slow frame silently becomes a dropped one. Here the page is a
 * pure function of t: we set t, wait for the paint, shoot. Same input, same
 * files, every time.
 */
import { chromium } from "playwright";
import { mkdir, rm } from "node:fs/promises";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const arg = (n, d) => { const i = process.argv.indexOf(`--${n}`); return i === -1 ? d : process.argv[i + 1]; };
const MODE = process.argv.includes("--beats") ? "beats"
           : process.argv.includes("--frames") ? "frames" : null;
if (!MODE) {
  console.error("usage: node shoot.mjs --beats|--frames [--reel 01] [--fps 30] [--scale 2] [--theme dark|paper|manim]");
  process.exit(2);
}
const REEL = arg("reel", "01");
const THEME = arg("theme", "dark");
const FPS = Number(arg("fps", 30));   // 45s cuts: 30fps is smooth for motion this slow and halves the shoot
const SCALE = MODE === "beats" ? 1 : Number(arg("scale", 2)); // 540x960 css * 2 = 1080x1920
const OUT = path.join(HERE, `${MODE}-${REEL}`);

await rm(OUT, { recursive: true, force: true });
await mkdir(OUT, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 540, height: 960 }, deviceScaleFactor: SCALE });
const errors = [];
page.on("pageerror", (e) => errors.push(e.message));
await page.goto("file://" + path.join(HERE, `reel${REEL}.html`));
await page.evaluate((t) => document.documentElement.setAttribute("data-theme", t), THEME);
// Fonts must be resolved before the first shot or frame 0 ships in a fallback face.
await page.evaluate(() => document.fonts.ready);

if (MODE === "beats") {
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
} else {
  const total = await page.evaluate(() => window.T_TOTAL);
  const frames = Math.round((total / 1000) * FPS);

  for (let i = 0; i < frames; i++) {
    await page.evaluate((t) => window.seek(t), (i * 1000) / FPS);
    await page.screenshot({ path: path.join(OUT, `f${String(i).padStart(4, "0")}.png`) });
    if (i % 60 === 0) process.stdout.write(`\r  frame ${i}/${frames}`);
  }
  process.stdout.write(`\r  frame ${frames}/${frames}\n`);

  await browser.close();
  console.log(`${frames} frames -> ${OUT}/ (${total}ms @ ${FPS}fps, ${540 * SCALE}x${960 * SCALE})`);
}
