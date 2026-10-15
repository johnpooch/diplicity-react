import { describe, expect, test } from "vitest";
import type { RunSummary } from "./api";
import { sortRuns } from "./runTable";

const run = (name: string, created: string, overrides: Partial<RunSummary> = {}): RunSummary => ({
  name,
  id: name,
  epochs: 30,
  model: "anthropic/claude-haiku-5-5",
  created,
  prompt: null,
  answers: 30,
  failed: 0,
  reasonable: 0,
  unreasonable: 0,
  unmarked: 0,
  order_sets: 0,
  new: 0,
  input_tokens: 0,
  output_tokens: 0,
  score: null,
  fixture_ids: ["paris_opening"],
  ...overrides,
});

const names = (runs: RunSummary[]) => runs.map(entry => entry.name);

describe("sortRuns", () => {
  const older = run("older", "2026-10-13T11:09:50+00:00", { prompt: "calm-lantern-oct-13", reasonable: 14 });
  const newer = run("newer", "2026-10-15T17:04:02+00:00", { prompt: "idle-comet-oct-15", reasonable: 11 });
  const unnamed = run("unnamed", "2026-10-14T09:00:00+00:00", {
    model: "anthropic/claude-haiku-4-5",
    answers: 2,
    failed: 2,
  });

  test("sorts by date in either direction", () => {
    expect(names(sortRuns([older, unnamed, newer], "created", "desc"))).toEqual(["newer", "unnamed", "older"]);
    expect(names(sortRuns([older, unnamed, newer], "created", "asc"))).toEqual(["older", "unnamed", "newer"]);
  });

  test("runs without a prompt name or a usable answer sort last in either direction", () => {
    expect(names(sortRuns([unnamed, newer, older], "prompt", "asc"))).toEqual(["older", "newer", "unnamed"]);
    expect(names(sortRuns([unnamed, newer, older], "prompt", "desc"))).toEqual(["newer", "older", "unnamed"]);
    expect(names(sortRuns([unnamed, newer, older], "score", "desc"))).toEqual(["older", "newer", "unnamed"]);
  });

  test("a lucky single answer does not outrank a steady score on many", () => {
    const lucky = run("lucky", "2026-10-08T21:17:15+00:00", { answers: 1, reasonable: 1 });
    expect(names(sortRuns([lucky, newer, older], "score", "desc"))).toEqual(["older", "newer", "lucky"]);
  });

  test("ties keep the newest run first", () => {
    expect(names(sortRuns([older, newer, unnamed], "model", "desc"))).toEqual(["newer", "older", "unnamed"]);
  });

  test("sorts by how many fixtures a run covers", () => {
    const wide = run("wide", "2026-10-01T00:00:00+00:00", { fixture_ids: ["a", "b", "c"] });
    expect(names(sortRuns([older, wide], "fixtures", "desc"))).toEqual(["wide", "older"]);
  });
});
