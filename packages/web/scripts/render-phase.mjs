#!/usr/bin/env vite-node
// Renders a phase RenderState to a PNG using the real board renderer, with no
// dev server, browser app, or backend running. Reads a RenderState JSON (as
// emitted by the backend `dump_phase` command), composes the board SVG via
// DiplicityMap, and rasterises it through the bundled headless Chromium.
//
// Must be run with vite-node so the TypeScript renderer imports resolve.
//
// Usage:
//   npx vite-node scripts/render-phase.mjs <render-state.json> <output.png> [options]
//
// Options:
//   --dsvg PATH   Board .d.svg to render onto
//                 (default: service/variant/data/svg/classical.d.svg)
//   --width PX    Output width in pixels (default 1600)

import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { chromium } from "playwright";
import { JSDOM } from "jsdom";
import { DiplicityMap } from "../src/components/InteractiveMap/mapRenderer";

globalThis.DOMParser = new JSDOM().window.DOMParser;

const here = dirname(fileURLToPath(import.meta.url));
const repoRoot = resolve(here, "../../..");

const args = process.argv.slice(2);
const positional = args.filter(a => !a.startsWith("--"));
if (positional.length < 2) {
  console.error(
    "Usage: npx vite-node scripts/render-phase.mjs <render-state.json> <output.png> [--dsvg PATH] [--width PX]"
  );
  process.exit(1);
}
const [statePath, outputPath] = positional;

const getOption = name => {
  const index = args.indexOf(`--${name}`);
  return index === -1 ? null : args[index + 1];
};

const dsvgPath = getOption("dsvg") ?? resolve(repoRoot, "service/variant/data/svg/classical.d.svg");
const width = Number(getOption("width") ?? 1600);

const state = JSON.parse(readFileSync(statePath, "utf8"));
const dsvg = readFileSync(dsvgPath, "utf8");
const rawSvg = new DiplicityMap(dsvg).render(state);

const viewBox = rawSvg.match(/viewBox="([\d.\- ]+)"/);
if (!viewBox) {
  throw new Error("rendered SVG has no viewBox");
}
const [, , vw, vh] = viewBox[1].split(/\s+/).map(Number);
const height = Math.round((width * vh) / vw);
const svg = rawSvg.replace("<svg ", `<svg width="${width}" height="${height}" `);

const resolveExecutablePath = async () => {
  try {
    const probe = await chromium.launch({ headless: true });
    await probe.close();
    return undefined;
  } catch {
    return (await import("@sparticuz/chromium")).default.executablePath();
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
  await page.setContent(
    `<!doctype html><html><body style="margin:0">${svg}</body></html>`,
    { waitUntil: "networkidle" }
  );
  const element = await page.$("svg");
  if (!element) {
    throw new Error("no svg element on page");
  }
  await element.screenshot({ path: outputPath });
  console.log(`Saved ${outputPath} (${width}x${height} from ${dsvgPath})`);
} finally {
  await browser.close();
}
