/**
 * Renders og.html to sell/public/og.png, the 1200x630 card a link to the sell
 * page unfurls into. Lives here rather than in sell/ so Playwright stays out
 * of the product's dependency tree (see package.json).
 *
 *   node og.mjs
 */
import { chromium } from "playwright";
import { fileURLToPath } from "node:url";
import path from "node:path";

const HERE = path.dirname(fileURLToPath(import.meta.url));
const OUT = path.join(HERE, "..", "sell", "public", "og.png");

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1200, height: 630 }, deviceScaleFactor: 1 });
await page.goto("file://" + path.join(HERE, "og.html"));
await page.evaluate(() => document.fonts.ready);
await page.screenshot({ path: OUT });
await browser.close();
console.log("wrote", OUT);
