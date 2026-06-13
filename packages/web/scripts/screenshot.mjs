#!/usr/bin/env node
// Takes a screenshot of the running dev server using Playwright.
//
// Usage:
//   node scripts/screenshot.mjs <path> <output.png> [options]
//
// Examples:
//   node scripts/screenshot.mjs / /tmp/my-games.png
//   node scripts/screenshot.mjs /game/active-movement/phase/101/orders /tmp/orders.png
//   node scripts/screenshot.mjs / /tmp/mobile.png --viewport 390x844
//
// Options:
//   --viewport WxH   Viewport size (default 1280x800)
//   --base URL       Dev server base URL (default http://localhost:5173)
//   --full-page      Capture the full scrollable page
//   --logged-out     Clear auth tokens so the logged-out UI renders
//   --wait MS        Extra settle time after network idle (default 1000)

import { chromium } from "playwright";

const args = process.argv.slice(2);
const positional = args.filter(a => !a.startsWith("--"));
if (positional.length < 2) {
  console.error(
    "Usage: node scripts/screenshot.mjs <path> <output.png> [--viewport WxH] [--base URL] [--full-page] [--logged-out] [--wait MS]"
  );
  process.exit(1);
}
const [pagePath, outputPath] = positional;

const getOption = name => {
  const index = args.indexOf(`--${name}`);
  return index === -1 ? null : args[index + 1];
};

const base = getOption("base") ?? "http://localhost:5173";
const viewportArg = getOption("viewport") ?? "1280x800";
const [width, height] = viewportArg.split("x").map(Number);
const fullPage = args.includes("--full-page");
const loggedOut = args.includes("--logged-out");
const settleMs = Number(getOption("wait") ?? 1000);

const resolveExecutablePath = async () => {
  try {
    const probe = await chromium.launch({ headless: true });
    await probe.close();
    return undefined;
  } catch {
    const sparticuz = (await import("@sparticuz/chromium")).default;
    return sparticuz.executablePath();
  }
};

const executablePath = await resolveExecutablePath();
const browser = await chromium.launch({
  headless: true,
  executablePath,
  args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
});

try {
  const context = await browser.newContext({ viewport: { width, height } });
  const page = await context.newPage();

  if (loggedOut) {
    await context.addInitScript(() => {
      localStorage.clear();
      localStorage.setItem("mock:loggedOut", "true");
    });
  }

  page.on("pageerror", error => console.error("[pageerror]", error.message));
  page.on("console", message => {
    if (message.type() === "error") {
      console.error("[console.error]", message.text().slice(0, 300));
    }
  });

  const url = new URL(pagePath, base).toString();
  await page.goto(url, { waitUntil: "networkidle", timeout: 60000 });
  await page.waitForTimeout(settleMs);
  await page.screenshot({ path: outputPath, fullPage });
  console.log(`Saved ${outputPath} (${url} @ ${width}x${height})`);
} finally {
  await browser.close();
}
