#!/usr/bin/env vite-node
// Captures every screen in the manifest at every viewport, into a directory.
//
// Must be run with vite-node so the manifest's fixture imports resolve.
//
// Determinism matters more than fidelity here: captures are compared against
// each other, so anything varying between two runs of the same commit is a
// false diff. The clock is fixed, animations are disabled, locale and timezone
// are pinned, requests to third-party origins are blocked, notifications are
// granted so the permission warning never fires, and toasts are hidden because
// they dismiss on a timer.
//
// Usage:
//   npx vite-node scripts/screenshot-diff/capture.mjs <output-dir> [options]
//
// Options:
//   --base URL         Server base URL (default http://localhost:5173)
//   --concurrency N    Pages captured in parallel (default 4)
//   --only SUBSTRING   Capture only screens whose name contains SUBSTRING
//   --screens FILE     Capture only the "<screen>__<viewport>" names in FILE
//   --offline          Block webfonts too, for runs with no network
//   --require-fonts    Fail if the webfont did not load on every screen
//   --allow-failures   Exit 0 even when screens fail, for baseline captures

import { mkdir, readFile, writeFile } from "node:fs/promises";
import { join } from "node:path";
import { launchChromium } from "../chromium.mjs";
import { screens, viewports } from "./manifest.mjs";

const FIXED_TIME = new Date("2026-01-01T12:00:00Z");
const SETTLE_POLL_MS = 100;
const SETTLE_STABLE_POLLS = 3;
const READY_TIMEOUT_MS = 15000;
const STABLE_FRAMES = 3;
const FRAME_INTERVAL_MS = 300;
const MAX_FRAMES = 25;
const FONT_ORIGINS = ["fonts.googleapis.com", "fonts.gstatic.com"];
const FONT_PROBE = '16px "Cabin"';

const args = process.argv.slice(2);
const positional = args.filter(a => !a.startsWith("--"));
if (positional.length < 1) {
  console.error(
    "Usage: npx vite-node scripts/screenshot-diff/capture.mjs <output-dir> [--base URL] [--concurrency N] [--only SUBSTRING] [--offline] [--require-fonts] [--allow-failures]"
  );
  process.exit(1);
}
const [outputDir] = positional;

const getOption = name => {
  const index = args.indexOf(`--${name}`);
  return index === -1 ? null : args[index + 1];
};

const base = getOption("base") ?? "http://localhost:5173";
const concurrency = Number(getOption("concurrency") ?? 4);
const only = getOption("only");
const screensFile = getOption("screens");
const offline = args.includes("--offline");
const requireFonts = args.includes("--require-fonts");
const allowFailures = args.includes("--allow-failures");

const disableAnimations = `
  *, *::before, *::after {
    animation-duration: 0s !important;
    animation-delay: 0s !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0s !important;
    transition-delay: 0s !important;
    caret-color: transparent !important;
  }
  html { scroll-behavior: auto !important; }
  [data-sonner-toaster] { display: none !important; }
`;

const noVisiblePlaceholders = () => {
  const blocks = el => {
    const r = el.getBoundingClientRect();
    if (r.width === 0 || r.height === 0) return true;
    return (
      r.bottom > 0 &&
      r.right > 0 &&
      r.top < window.innerHeight &&
      r.left < window.innerWidth
    );
  };
  const selector = '[data-slot="skeleton"], .animate-pulse';
  return !Array.from(document.querySelectorAll(selector)).some(blocks);
};

const waitForReady = async page => {
  await page.waitForFunction(
    () => {
      const root = document.getElementById("root");
      return Boolean(root) && root.childElementCount > 0;
    },
    null,
    { timeout: READY_TIMEOUT_MS }
  );

  try {
    await page.evaluate(() => document.fonts.ready);
  } catch {
    await page.waitForLoadState("networkidle");
    await page.evaluate(() => document.fonts.ready);
  }

  await page
    .waitForFunction(
      () => Array.from(document.images).every(image => image.complete),
      null,
      { timeout: READY_TIMEOUT_MS }
    )
    .catch(() => {});

  await page
    .evaluate(async () => {
      const urls = new Set();
      for (const element of document.querySelectorAll("*")) {
        const value = getComputedStyle(element).backgroundImage;
        if (!value || value === "none") continue;
        for (const match of value.matchAll(/url\(["']?(.*?)["']?\)/g)) {
          urls.add(match[1]);
        }
      }
      await Promise.all(
        [...urls].map(
          url =>
            new Promise(resolve => {
              const image = new Image();
              image.onload = resolve;
              image.onerror = resolve;
              image.src = url;
            })
        )
      );
    })
    .catch(() => {});

  const domStable = page.waitForFunction(
    ([pollMs, stablePolls]) => {
      const state = (window.__shotStability ??= { last: null, count: 0 });
      const now = document.body?.innerHTML.length ?? 0;
      if (now === state.last) state.count += 1;
      else {
        state.last = now;
        state.count = 0;
      }
      return state.count >= stablePolls;
    },
    [SETTLE_POLL_MS, SETTLE_STABLE_POLLS],
    { polling: SETTLE_POLL_MS, timeout: READY_TIMEOUT_MS }
  );

  const noPlaceholders = page.waitForFunction(noVisiblePlaceholders, null, {
    polling: SETTLE_POLL_MS,
    timeout: READY_TIMEOUT_MS,
  });

  const settled = await Promise.all([
    domStable.then(
      () => true,
      () => false
    ),
    noPlaceholders.then(
      () => true,
      () => false
    ),
  ]);

  const fontsLoaded = await page.evaluate(
    probe => document.fonts.check(probe),
    FONT_PROBE
  );

  return {
    domSettled: settled[0],
    placeholdersCleared: settled[1],
    fontsLoaded,
  };
};

const captureStableFrame = async page => {
  const frames = [];
  for (let attempt = 0; attempt < MAX_FRAMES; attempt += 1) {
    const frame = await page.screenshot();
    frames.push(frame);
    const recent = frames.slice(-STABLE_FRAMES);
    if (
      recent.length === STABLE_FRAMES &&
      recent.every(candidate => candidate.equals(recent[0]))
    ) {
      return { buffer: recent[0], visuallyStable: true, frames: frames.length };
    }
    await page.waitForTimeout(FRAME_INTERVAL_MS);
  }
  return {
    buffer: frames[frames.length - 1],
    visuallyStable: false,
    frames: frames.length,
  };
};

const captureOne = async (browser, screen, viewport) => {
  const context = await browser.newContext({
    viewport: { width: viewport.width, height: viewport.height },
    deviceScaleFactor: 1,
    colorScheme: "light",
    reducedMotion: "reduce",
    locale: "en-GB",
    timezoneId: "UTC",
    permissions: ["notifications"],
  });

  await context.route("**/*", route => {
    const url = new URL(route.request().url());
    if (url.origin === new URL(base).origin) return route.continue();
    if (!offline && FONT_ORIGINS.includes(url.hostname)) return route.continue();
    return route.abort();
  });

  await context.addInitScript(
    ([shouldLogOut, css]) => {
      if (shouldLogOut) {
        localStorage.clear();
        localStorage.setItem("mock:loggedOut", "true");
      }

      const NativeIntersectionObserver = window.IntersectionObserver;
      if (NativeIntersectionObserver) {
        window.IntersectionObserver = class extends NativeIntersectionObserver {
          constructor(callback, options) {
            super(callback, {
              ...(options ?? {}),
              root: null,
              rootMargin: "100000px",
            });
          }
        };
      }

      const apply = () => {
        const style = document.createElement("style");
        style.textContent = css;
        document.head?.appendChild(style);
      };
      if (document.head) apply();
      else document.addEventListener("DOMContentLoaded", apply);
    },
    [screen.loggedOut, disableAnimations]
  );

  const page = await context.newPage();
  await page.clock.setFixedTime(FIXED_TIME);

  const pageErrors = [];
  page.on("pageerror", error => pageErrors.push(error.message));

  const name = `${screen.name}__${viewport.name}`;
  try {
    await page.goto(new URL(screen.path, base).toString(), {
      waitUntil: "networkidle",
      timeout: 60000,
    });
    const ready = await waitForReady(page);
    const frame = await captureStableFrame(page);
    await writeFile(join(outputDir, `${name}.png`), frame.buffer);
    return {
      name,
      ok: pageErrors.length === 0 && frame.visuallyStable,
      ...ready,
      visuallyStable: frame.visuallyStable,
      frames: frame.frames,
      errors: frame.visuallyStable
        ? pageErrors
        : [...pageErrors, "never reached a visually stable frame"],
    };
  } catch (error) {
    return {
      name,
      ok: false,
      domSettled: false,
      placeholdersCleared: false,
      fontsLoaded: false,
      visuallyStable: false,
      errors: [...pageErrors, error.message],
    };
  } finally {
    await context.close();
  }
};

const run = async () => {
  await mkdir(outputDir, { recursive: true });

  const wanted = screensFile
    ? new Set(
        (await readFile(screensFile, "utf8"))
          .split("\n")
          .map(line => line.trim())
          .filter(Boolean)
      )
    : null;

  const jobs = screens
    .filter(screen => !only || screen.name.includes(only))
    .flatMap(screen => viewports.map(viewport => ({ screen, viewport })))
    .filter(
      job => !wanted || wanted.has(`${job.screen.name}__${job.viewport.name}`)
    );

  const browser = await launchChromium();

  const results = [];
  let cursor = 0;
  const worker = async () => {
    while (cursor < jobs.length) {
      const job = jobs[cursor++];
      const result = await captureOne(browser, job.screen, job.viewport);
      results.push(result);
      const status = result.ok ? "ok" : "FAIL";
      console.log(`[${results.length}/${jobs.length}] ${status} ${result.name}`);
    }
  };

  await Promise.all(
    Array.from({ length: Math.min(concurrency, jobs.length) }, worker)
  );
  await browser.close();

  results.sort((a, b) => a.name.localeCompare(b.name));
  await writeFile(
    join(outputDir, "capture-report.json"),
    `${JSON.stringify(results, null, 2)}\n`
  );

  const failures = results.filter(result => !result.ok);
  const missingFonts = results.filter(result => result.ok && !result.fontsLoaded);
  const unsettled = results.filter(
    result => result.ok && (!result.domSettled || !result.placeholdersCleared)
  );
  console.log(`\nCaptured ${results.length - failures.length}/${results.length}`);
  for (const result of unsettled) {
    console.warn(`WARN ${result.name}: did not fully settle before capture`);
  }
  for (const failure of failures) {
    console.error(`FAIL ${failure.name}: ${failure.errors.join(" | ")}`);
  }
  if (requireFonts && missingFonts.length > 0) {
    console.error(
      `\nFAIL webfont did not load on ${missingFonts.length} screen(s); aborting rather than reporting false differences`
    );
    process.exit(1);
  }
  if (failures.length > 0 && !allowFailures) process.exit(1);
};

await run();
