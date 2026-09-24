#!/usr/bin/env node
// Compares two capture directories and writes a composite image per changed
// screen, plus a JSON report naming what changed.
//
// Each composite is three panels left to right: base, head, difference.
//
// Usage:
//   node scripts/screenshot-diff/compare.mjs <base-dir> <head-dir> <out-dir>
//
// Options:
//   --threshold N   Per-pixel colour distance, 0-1 (default 0.1)
//   --min-pixels N  Ignore diffs smaller than N pixels (default 0)

import { mkdir, readdir, writeFile } from "node:fs/promises";
import { readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import { PNG } from "pngjs";
import pixelmatch from "pixelmatch";

const GUTTER = 8;
const BACKGROUND = [235, 237, 240, 255];

const args = process.argv.slice(2);
const positional = args.filter(a => !a.startsWith("--"));
if (positional.length < 3) {
  console.error(
    "Usage: node scripts/screenshot-diff/compare.mjs <base-dir> <head-dir> <out-dir> [--threshold N] [--min-pixels N]"
  );
  process.exit(1);
}
const [baseDir, headDir, outDir] = positional;

const getOption = name => {
  const index = args.indexOf(`--${name}`);
  return index === -1 ? null : args[index + 1];
};

const threshold = Number(getOption("threshold") ?? 0.1);
const minPixels = Number(getOption("min-pixels") ?? 0);

const listShots = async dir => {
  try {
    const entries = await readdir(dir);
    return new Set(entries.filter(name => name.endsWith(".png")));
  } catch {
    return new Set();
  }
};

const readPng = path => PNG.sync.read(readFileSync(path));

const padTo = (png, width, height) => {
  if (png.width === width && png.height === height) return png;
  const padded = new PNG({ width, height });
  for (let i = 0; i < padded.data.length; i += 4) {
    padded.data.set(BACKGROUND, i);
  }
  PNG.bitblt(png, padded, 0, 0, png.width, png.height, 0, 0);
  return padded;
};

const composite = (panels, width, height) => {
  const out = new PNG({
    width: panels.length * width + (panels.length - 1) * GUTTER,
    height,
  });
  for (let i = 0; i < out.data.length; i += 4) {
    out.data.set(BACKGROUND, i);
  }
  panels.forEach((panel, index) => {
    PNG.bitblt(
      panel,
      out,
      0,
      0,
      width,
      height,
      index * (width + GUTTER),
      0
    );
  });
  return out;
};

const compareOne = (name, basePath, headPath) => {
  const basePng = readPng(basePath);
  const headPng = readPng(headPath);
  const width = Math.max(basePng.width, headPng.width);
  const height = Math.max(basePng.height, headPng.height);
  const a = padTo(basePng, width, height);
  const b = padTo(headPng, width, height);

  const diff = new PNG({ width, height });
  const changedPixels = pixelmatch(a.data, b.data, diff.data, width, height, {
    threshold,
    includeAA: false,
    alpha: 0.4,
  });

  if (changedPixels <= minPixels) return { name, changedPixels, changed: false };

  const sheet = composite([a, b, diff], width, height);
  writeFileSync(join(outDir, `${name}.png`), PNG.sync.write(sheet));
  return {
    name,
    changedPixels,
    changed: true,
    percent: Number(((100 * changedPixels) / (width * height)).toFixed(3)),
    file: `${name}.png`,
  };
};

const run = async () => {
  await mkdir(outDir, { recursive: true });

  const baseShots = await listShots(baseDir);
  const headShots = await listShots(headDir);

  const added = [...headShots].filter(name => !baseShots.has(name)).sort();
  const removed = [...baseShots].filter(name => !headShots.has(name)).sort();
  const common = [...headShots].filter(name => baseShots.has(name)).sort();

  const compared = common.map(file => {
    const name = file.replace(/\.png$/, "");
    return compareOne(name, join(baseDir, file), join(headDir, file));
  });

  const changed = compared
    .filter(result => result.changed)
    .sort((a, b) => b.changedPixels - a.changedPixels);

  const report = {
    total: common.length + added.length,
    changed,
    added: added.map(name => name.replace(/\.png$/, "")),
    removed: removed.map(name => name.replace(/\.png$/, "")),
  };

  await writeFile(
    join(outDir, "diff-report.json"),
    `${JSON.stringify(report, null, 2)}\n`
  );

  console.log(
    `${changed.length} changed, ${added.length} added, ${removed.length} removed, of ${report.total} screens`
  );
  for (const result of changed) {
    console.log(`  ${result.name}  ${result.changedPixels}px (${result.percent}%)`);
  }
};

await run();
