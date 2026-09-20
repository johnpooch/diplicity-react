#!/usr/bin/env node
// Renders the pull request comment body from a diff report.
//
// Usage:
//   node scripts/screenshot-diff/comment.mjs <diff-report.json> <image-base-url>
//
// Options:
//   --max N   Screens embedded as images; the rest are listed (default 20)

import { readFileSync } from "node:fs";

export const MARKER = "<!-- screenshot-diff -->";

const args = process.argv.slice(2);
const positional = args.filter(a => !a.startsWith("--"));
if (positional.length < 2) {
  console.error(
    "Usage: node scripts/screenshot-diff/comment.mjs <diff-report.json> <image-base-url> [--max N]"
  );
  process.exit(1);
}
const [reportPath, imageBaseUrl] = positional;

const getOption = name => {
  const index = args.indexOf(`--${name}`);
  return index === -1 ? null : args[index + 1];
};

const max = Number(getOption("max") ?? 20);
const report = JSON.parse(readFileSync(reportPath, "utf8"));
const trimmedBase = imageBaseUrl.replace(/\/$/, "");

const plural = (count, word) => `${count} ${word}${count === 1 ? "" : "s"}`;

const summary = () => {
  const parts = [`${plural(report.changed.length, "screen")} changed`];
  if (report.added.length > 0) parts.push(`${report.added.length} added`);
  if (report.removed.length > 0) parts.push(`${report.removed.length} removed`);
  return `${parts.join(", ")} of ${report.total} captured.`;
};

const section = entry => {
  const url = `${trimmedBase}/${entry.file}`;
  const heading = `<b>${entry.name}</b> — ${entry.changedPixels.toLocaleString()} px (${entry.percent}%)`;
  return [
    `<details open>`,
    `<summary>${heading}</summary>`,
    ``,
    `<a href="${url}"><img src="${url}" width="960" alt="${entry.name}"></a>`,
    ``,
    `</details>`,
  ].join("\n");
};

const lines = [MARKER, "", "## Screenshot diff", "", summary()];

if (report.changed.length === 0 && report.added.length === 0) {
  lines.push("", "No visual differences found.");
} else {
  lines.push(
    "",
    "Each image is three panels left to right: **base**, **this PR**, **difference**. Click to view full size."
  );

  const embedded = report.changed.slice(0, max);
  const overflow = report.changed.slice(max);

  for (const entry of embedded) lines.push("", section(entry));

  if (overflow.length > 0) {
    lines.push(
      "",
      `<details><summary>${plural(overflow.length, "further changed screen")}</summary>`,
      ""
    );
    for (const entry of overflow) {
      lines.push(`- ${entry.name} — ${entry.changedPixels.toLocaleString()} px`);
    }
    lines.push("", "</details>");
  }

  if (report.added.length > 0) {
    lines.push(
      "",
      `<details><summary>${plural(report.added.length, "new screen")}</summary>`,
      ""
    );
    for (const name of report.added) lines.push(`- ${name}`);
    lines.push("", "</details>");
  }

  if (report.removed.length > 0) {
    lines.push(
      "",
      `<details><summary>${plural(report.removed.length, "removed screen")}</summary>`,
      ""
    );
    for (const name of report.removed) lines.push(`- ${name}`);
    lines.push("", "</details>");
  }
}

console.log(lines.join("\n"));
