/* Records the sell page's rep (watch, lock, rebuild, grade, reveal) as the
   launch-day screen recording. Lives here, not in deck/, so it can borrow
   this package's Playwright. Serve dist first:
     python3 -m http.server 4173 --directory dist
   then:  node launch-demo.mjs   ->  ../deck/launch-demo.mp4 */
import { chromium } from "playwright";
import { execFileSync } from "node:child_process";
import { rmSync } from "node:fs";

const URL = process.env.URL ?? "http://localhost:4173/#rep";
// Deliberately imperfect: hits 4 of the 6 rubric keys and never mentions a
// TTL, so probe 2 (the stale-write race) lands on a real gap.
const ANSWER =
  "The app checks the cache for the product key. On a miss the app queries the database itself, then writes the value into the cache so the next read hits.";

const browser = await chromium.launch();
const ctx = await browser.newContext({
  viewport: { width: 1280, height: 720 },
  recordVideo: { dir: "video-tmp", size: { width: 1280, height: 720 } },
});
const page = await ctx.newPage();
await page.goto(URL, { waitUntil: "networkidle" });
await page.locator("#rep").scrollIntoViewIfNeeded();
await page.waitForTimeout(2500);
await page.getByRole("button", { name: /watch the rep/ }).click();
await page.getByRole("button", { name: /submit, no going back/ }).waitFor({ timeout: 60_000 });
await page.waitForTimeout(1500);
await page.locator("#recall").pressSequentially(ANSWER, { delay: 40 });
await page.waitForTimeout(1500);
await page.getByRole("button", { name: /submit, no going back/ }).click();
await page.waitForTimeout(7000);
await page.locator(".probe").first().scrollIntoViewIfNeeded();
await page.waitForTimeout(7000);
await page.getByRole("button", { name: /show the diagram again/ }).click();
await page.waitForTimeout(8000);
const webm = await page.video().path();
await ctx.close();
await browser.close();
execFileSync("ffmpeg", ["-y", "-loglevel", "error", "-i", webm, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "30", "-movflags", "+faststart", "../deck/launch-demo.mp4"]);
rmSync("video-tmp", { recursive: true, force: true });
console.log("wrote ../deck/launch-demo.mp4");
