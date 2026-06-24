#!/usr/bin/env node
// Map performance benchmark harness (Block 1 of the map re-architecture).
//
// Drives a fixed pan/zoom gesture on the CURRENT map (react-zoom-pan-pinch + dSVG)
// in headless Chromium under CDP CPU throttling, captures frame cadence via an injected
// requestAnimationFrame recorder, and writes a committed JSON baseline + stdout table.
// It changes nothing in the app: all metrics are captured externally.
//
// Prereq: the mock dev server must be running:
//   npm --prefix ../web run dev:mocks    # serves real SVGs via MSW at http://localhost:5173
//
// Usage:
//   node scripts/map-bench.mjs [options]
//
// Options:
//   --base URL          Dev server base URL (default http://localhost:5173)
//   --reps N            Repetitions per cell, median reported (default 3)
//   --cpu a,b,c         CPU throttle tiers (default 1,4,6)
//   --viewports WxH,... Viewport tiers (default 1280x800,390x844)
//   --out PATH          Working JSON output path (default bench/results.json)
//   --write-baseline    Also write bench/baseline.json
//   --wait MS           Extra settle time after readiness gate (default 1000)

import { chromium } from "playwright";
import { execSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const PACKAGE_ROOT = resolve(HERE, "..");

const FRAME_BUDGET_MS = 1000 / 60;
const DROPPED_THRESHOLD = 1.5;
const WARMUP_MS = 200;
const GESTURE = { zoomTicks: 12, panSteps: 40, wheelIntervalMs: 40, panIntervalMs: 16, settleMs: 300 };

const FIXTURES = [
  {
    name: "classical-active-movement",
    route: "/game/active-movement/phase/101",
  },
];

const args = process.argv.slice(2);
const getOption = name => {
  const index = args.indexOf(`--${name}`);
  return index === -1 ? null : args[index + 1];
};

const base = getOption("base") ?? "http://localhost:5173";
const reps = Number(getOption("reps") ?? 3);
const cpuTiers = (getOption("cpu") ?? "1,4,6").split(",").map(Number);
const viewports = (getOption("viewports") ?? "1280x800,390x844").split(",");
const outPath = resolve(PACKAGE_ROOT, getOption("out") ?? "bench/results.json");
const writeBaseline = args.includes("--write-baseline");
const settleMs = Number(getOption("wait") ?? 1000);

const delay = ms => new Promise(r => setTimeout(r, ms));
const median = xs => {
  if (xs.length === 0) return 0;
  const s = [...xs].sort((a, b) => a - b);
  const mid = Math.floor(s.length / 2);
  return s.length % 2 ? s[mid] : (s[mid - 1] + s[mid]) / 2;
};
const percentile = (xs, p) => {
  if (xs.length === 0) return 0;
  const s = [...xs].sort((a, b) => a - b);
  const idx = Math.min(s.length - 1, Math.ceil((p / 100) * s.length) - 1);
  return s[Math.max(0, idx)];
};
const round = (n, d = 2) => Number(n.toFixed(d));

const resolveExecutablePath = async () => {
  try {
    const probe = await chromium.launch({ headless: true });
    await probe.close();
    return { executablePath: undefined, source: "system" };
  } catch {
    const sparticuz = (await import("@sparticuz/chromium")).default;
    return { executablePath: await sparticuz.executablePath(), source: "sparticuz-fallback" };
  }
};

// Injected before navigation. Records requestAnimationFrame timestamps into window.__mapBench
// only while recording is active. Purely external — never touches app source.
const rafRecorderInit = () => {
  window.__mapBench = { frames: [], recording: false };
  window.__mapBenchStart = () => {
    window.__mapBench.frames = [];
    window.__mapBench.recording = true;
    const loop = t => {
      if (!window.__mapBench.recording) return;
      window.__mapBench.frames.push(t);
      requestAnimationFrame(loop);
    };
    requestAnimationFrame(loop);
  };
  window.__mapBenchStop = () => {
    window.__mapBench.recording = false;
    return window.__mapBench.frames;
  };
};

const runGesture = async (cdp, center) => {
  const wheel = deltaY => cdp.send("Input.dispatchMouseEvent", { type: "mouseWheel", x: center.x, y: center.y, deltaX: 0, deltaY });
  for (let i = 0; i < GESTURE.zoomTicks; i++) {
    await wheel(-120);
    await delay(GESTURE.wheelIntervalMs);
  }
  await delay(GESTURE.settleMs);

  await cdp.send("Input.dispatchMouseEvent", { type: "mousePressed", x: center.x, y: center.y, button: "left", buttons: 1, clickCount: 1 });
  for (let i = 1; i <= GESTURE.panSteps; i++) {
    const f = i / GESTURE.panSteps;
    await cdp.send("Input.dispatchMouseEvent", {
      type: "mouseMoved",
      x: center.x - Math.round(f * 200),
      y: center.y - Math.round(f * 150),
      button: "left",
      buttons: 1,
    });
    await delay(GESTURE.panIntervalMs);
  }
  await cdp.send("Input.dispatchMouseEvent", { type: "mouseReleased", x: center.x - 200, y: center.y - 150, button: "left", buttons: 1, clickCount: 1 });
  await delay(GESTURE.settleMs);

  for (let i = 0; i < GESTURE.zoomTicks; i++) {
    await wheel(120);
    await delay(GESTURE.wheelIntervalMs);
  }
  await delay(GESTURE.settleMs);
};

const summarizeFrames = frames => {
  if (frames.length < 2) return { medianFrameMs: 0, p95FrameMs: 0, droppedFramePct: 0, frameCount: frames.length, effectiveFps: 0 };
  const t0 = frames[0];
  const kept = frames.filter(t => t - t0 >= WARMUP_MS);
  const deltas = [];
  for (let i = 1; i < kept.length; i++) deltas.push(kept[i] - kept[i - 1]);
  if (deltas.length === 0) return { medianFrameMs: 0, p95FrameMs: 0, droppedFramePct: 0, frameCount: kept.length, effectiveFps: 0 };
  const dropped = deltas.filter(d => d > DROPPED_THRESHOLD * FRAME_BUDGET_MS).length;
  const spanMs = kept[kept.length - 1] - kept[0];
  return {
    medianFrameMs: round(median(deltas)),
    p95FrameMs: round(percentile(deltas, 95)),
    droppedFramePct: round((dropped / deltas.length) * 100),
    frameCount: kept.length,
    effectiveFps: round(spanMs > 0 ? ((kept.length - 1) / spanMs) * 1000 : 0),
  };
};

const runRep = async (context, fixture, cpuThrottle) => {
  const page = await context.newPage();
  let initialRenderMs = null;
  page.on("console", msg => {
    if (initialRenderMs !== null) return;
    const m = msg.text().match(/renderer\.render\(\) took ([\d.]+)ms/);
    if (m) initialRenderMs = Number(m[1]);
  });
  page.on("pageerror", error => console.error("[pageerror]", error.message));

  await page.addInitScript(rafRecorderInit);
  const cdp = await context.newCDPSession(page);
  await cdp.send("Emulation.setCPUThrottlingRate", { rate: cpuThrottle });

  try {
    const url = new URL(fixture.route, base).toString();
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60000 });
    await page.waitForSelector(".react-transform-component svg", { timeout: 30000 });
    await page.waitForTimeout(settleMs);

    const box = await page.locator(".react-transform-component").first().boundingBox();
    const center = box
      ? { x: Math.round(box.x + box.width / 2), y: Math.round(box.y + box.height / 2) }
      : { x: 640, y: 400 };

    await page.evaluate(() => window.__mapBenchStart());
    await runGesture(cdp, center);
    const frames = await page.evaluate(() => window.__mapBenchStop());

    return { ...summarizeFrames(frames), initialRenderMs: initialRenderMs ?? 0 };
  } finally {
    await cdp.send("Emulation.setCPUThrottlingRate", { rate: 1 });
    await page.close();
  }
};

const gitInfo = () => {
  try {
    const commit = execSync("git rev-parse HEAD", { cwd: PACKAGE_ROOT }).toString().trim();
    const dirty = execSync("git status --porcelain", { cwd: PACKAGE_ROOT }).toString().trim().length > 0;
    return { commit, dirty };
  } catch {
    return { commit: "unknown", dirty: false };
  }
};

const { executablePath, source } = await resolveExecutablePath();
const browser = await chromium.launch({
  headless: true,
  executablePath,
  args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage"],
});

const results = [];
try {
  const chromiumVersion = source === "system" ? browser.version() : "sparticuz-fallback";
  for (const viewportArg of viewports) {
    const [width, height] = viewportArg.split("x").map(Number);
    const context = await browser.newContext({ viewport: { width, height } });
    try {
      for (const fixture of FIXTURES) {
        for (const cpuThrottle of cpuTiers) {
          const repResults = [];
          for (let r = 0; r < reps; r++) {
            repResults.push(await runRep(context, fixture, cpuThrottle));
          }
          const row = {
            fixture: fixture.name,
            route: fixture.route,
            viewport: viewportArg,
            cpuThrottle,
            initialRenderMs: round(median(repResults.map(x => x.initialRenderMs))),
            medianFrameMs: round(median(repResults.map(x => x.medianFrameMs))),
            p95FrameMs: round(median(repResults.map(x => x.p95FrameMs))),
            droppedFramePct: round(median(repResults.map(x => x.droppedFramePct))),
            frameCount: Math.round(median(repResults.map(x => x.frameCount))),
            effectiveFps: round(median(repResults.map(x => x.effectiveFps))),
          };
          results.push(row);
          console.log(
            `  ${row.viewport}  cpu ${row.cpuThrottle}x  median ${row.medianFrameMs}ms  p95 ${row.p95FrameMs}ms  dropped ${row.droppedFramePct}%  init ${row.initialRenderMs}ms  fps ${row.effectiveFps}`
          );
        }
      }
    } finally {
      await context.close();
    }
  }

  const output = {
    generatedAt: new Date().toISOString(),
    git: gitInfo(),
    environment: {
      harness: "map-bench.mjs",
      chromium: chromiumVersion,
      gpu: "disabled (--disable-gpu)",
      note: "headless software rendering; absolute fps not comparable to real devices",
    },
    gesture: {
      zoomTicks: GESTURE.zoomTicks,
      panSteps: GESTURE.panSteps,
      reps,
      frameBudgetMs: round(FRAME_BUDGET_MS),
      droppedThreshold: DROPPED_THRESHOLD,
    },
    results,
    notes: [
      "Only classical variant benchmarked: every mock game is wired to variantId 'classical'; godip coverage deferred.",
      "Absolute timings are headless + software-render; use only for before/after delta on the same machine/config.",
      "GPU compositing cost (the real-device hot path) is NOT captured here; real-user data is Block 2 (telemetry).",
    ],
  };

  mkdirSync(dirname(outPath), { recursive: true });
  writeFileSync(outPath, JSON.stringify(output, null, 2) + "\n");
  console.log(`\nWrote ${outPath}`);
  if (writeBaseline) {
    const baselinePath = resolve(PACKAGE_ROOT, "bench/baseline.json");
    writeFileSync(baselinePath, JSON.stringify(output, null, 2) + "\n");
    console.log(`Wrote ${baselinePath}`);
  }
  console.log("\nNotes:");
  for (const n of output.notes) console.log(`  - ${n}`);
} finally {
  await browser.close();
}
