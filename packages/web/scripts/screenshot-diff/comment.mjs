#!/usr/bin/env node
// Renders the pull request comment body from a diff report.
//
// The report describes the screens that were compared, which after the
// verification pass is only the candidates being re-checked. The total
// captured is a property of the capture, so it is passed in rather than
// inferred from the report.
//
// Usage:
//   node scripts/screenshot-diff/comment.mjs <diff-report.json> [options]
//
// Options:
//   --images URL   Base URL the difference images were published to. Without
//                  it the changed screens are listed rather than embedded.
//   --captured N   Screens captured in the full run (default: the report's own)
//   --max N        Screens embedded as images; the rest are listed (default 20)

import { readFileSync } from "node:fs";

export const MARKER = "<!-- screenshot-diff -->";

const args = process.argv.slice(2);
const [reportPath] = args;
if (!reportPath || reportPath.startsWith("--")) {
  console.error(
    "Usage: node scripts/screenshot-diff/comment.mjs <diff-report.json> [--images URL] [--captured N] [--max N]"
  );
  process.exit(1);
}

const getOption = name => {
  const index = args.indexOf(`--${name}`);
  return index === -1 ? null : args[index + 1];
};

const max = Number(getOption("max") ?? 20);
const report = JSON.parse(readFileSync(reportPath, "utf8"));
const captured = Number(getOption("captured") ?? report.total);
const imageBaseUrl = (getOption("images") ?? "").replace(/\/$/, "");
const canEmbed = imageBaseUrl !== "";

const plural = (count, word) => `${count} ${word}${count === 1 ? "" : "s"}`;

const summary = () => {
  const parts = [`${plural(report.changed.length, "screen")} changed`];
  if (report.added.length > 0) parts.push(`${report.added.length} added`);
  if (report.removed.length > 0) parts.push(`${report.removed.length} removed`);
  return `${parts.join(", ")} of ${captured} captured.`;
};

const describe = entry =>
  `${entry.name} — ${entry.changedPixels.toLocaleString()} px (${entry.percent}%)`;

const section = entry => {
  const url = `${imageBaseUrl}/${entry.file}`;
  return [
    `<details open>`,
    `<summary><b>${entry.name}</b> — ${entry.changedPixels.toLocaleString()} px (${entry.percent}%)</summary>`,
    ``,
    `<a href="${url}"><img src="${url}" width="960" alt="${entry.name}"></a>`,
    ``,
    `</details>`,
  ].join("\n");
};

const lines = [MARKER, "", "## Screenshot diff", "", summary()];

if (report.changed.length === 0 && report.added.length === 0) {
  lines.push("", "No visual differences found.");
} else if (!canEmbed) {
  lines.push(
    "",
    "Difference images were not published, so the changed screens are listed below. They are in the run's `screenshots` artifact."
  );
  for (const entry of report.changed) lines.push(`- ${describe(entry)}`);
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
    for (const entry of overflow) lines.push(`- ${describe(entry)}`);
    lines.push("", "</details>");
  }
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

console.log(lines.join("\n"));
