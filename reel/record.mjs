/**
 * Frame-steps a reel scene and writes one PNG per frame.
 *
 * Deterministic on purpose. Playwright's own recordVideo captures at whatever
 * rate the page happens to paint, so a slow frame silently becomes a dropped
 * one. Here the page is a pure function of t: we set t, wait for the paint,
 * shoot. Same input, same files, every time.
 *
 *   node record.mjs [--reel 01] [--fps 30] [--scale 2] [--theme dark|manim]
 */
import { chromium } from "playwright";
import { mkdir, rm } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const arg = (name, dflt) => {
  const i = process.argv.indexOf(`--${name}`);
  return i === -1 ? dflt : process.argv[i + 1];
};

const FPS = Number(arg("fps", 30));   // 45s cuts: 30fps is smooth for motion this slow and halves the shoot
const SCALE = Number(arg("scale", 2));      // 540x960 css * 2 = 1080x1920
const THEME = arg("theme", "dark");
const REEL = arg("reel", "01");
const OUT = path.join(HERE, `frames-${REEL}`);

await rm(OUT, { recursive: true, force: true });
await mkdir(OUT, { recursive: true });

const browser = await chromium.launch();
const page = await browser.newPage({
  viewport: { width: 540, height: 960 },
  deviceScaleFactor: SCALE,
});
await page.goto("file://" + path.join(HERE, `reel${REEL}.html`));
await page.evaluate((t) => document.documentElement.setAttribute("data-theme", t), THEME);
// Fonts must be resolved before the first shot or frame 0 ships in a fallback face.
await page.evaluate(() => document.fonts.ready);

const total = await page.evaluate(() => window.T_TOTAL);
const frames = Math.round((total / 1000) * FPS);

for (let i = 0; i < frames; i++) {
  await page.evaluate((t) => window.seek(t), (i * 1000) / FPS);
  await page.screenshot({ path: path.join(OUT, `f${String(i).padStart(4, "0")}.png`) });
  if (i % 60 === 0) process.stdout.write(`\r  frame ${i}/${frames}`);
}
process.stdout.write(`\r  frame ${frames}/${frames}\n`);

await browser.close();
console.log(`${frames} frames -> reel/frames/ (${total}ms @ ${FPS}fps, ${540 * SCALE}x${960 * SCALE})`);
