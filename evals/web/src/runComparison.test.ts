import { describe, expect, test } from "vitest";
import type { RunCounts, RunDetail } from "./api";
import { compareRuns } from "./runComparison";

type FixtureCounts = Pick<RunCounts, "answers" | "failed" | "reasonable"> & { id: string };

const counts = (fixture: FixtureCounts) => ({
  unreasonable: 0,
  unmarked: fixture.answers - fixture.failed - fixture.reasonable,
  order_sets: 0,
  new: 0,
  input_tokens: 0,
  output_tokens: 0,
  score: null,
  nation: "France",
  phase: { season: "Spring", year: 1901, type: "Movement" },
  ...fixture,
});

const detail = (name: string, fixtures: FixtureCounts[]): RunDetail => ({
  ...counts({ id: name, answers: 0, failed: 0, reasonable: 0 }),
  name,
  epochs: 30,
  model: "anthropic/claude-haiku-5-5",
  created: "2026-10-15T17:04:02+00:00",
  prompt: null,
  fixtures: fixtures.map(counts),
});

describe("compareRuns", () => {
  test("only the fixtures both runs cover are compared", () => {
    const run = detail("run", [
      { id: "england", answers: 30, failed: 0, reasonable: 11 },
      { id: "austria", answers: 30, failed: 0, reasonable: 30 },
    ]);
    const other = detail("other", [
      { id: "england", answers: 30, failed: 0, reasonable: 14 },
      { id: "france", answers: 30, failed: 0, reasonable: 0 },
    ]);
    const comparison = compareRuns(run, other)!;
    expect(comparison.fixtures).toEqual(["england"]);
    expect([comparison.here.reasonable, comparison.here.answers]).toEqual([11, 30]);
    expect([comparison.there.reasonable, comparison.there.answers]).toEqual([14, 30]);
  });

  test("runs that share no fixture are not compared", () => {
    const run = detail("run", [{ id: "england", answers: 30, failed: 0, reasonable: 11 }]);
    const other = detail("other", [{ id: "austria", answers: 1, failed: 0, reasonable: 1 }]);
    expect(compareRuns(run, other)).toBeNull();
  });

  test("a small swing on thirty answers is within the noise", () => {
    const run = detail("run", [{ id: "england", answers: 30, failed: 0, reasonable: 11 }]);
    const other = detail("other", [{ id: "england", answers: 30, failed: 0, reasonable: 14 }]);
    expect(compareRuns(run, other)!.overlapping).toBe(true);
  });

  test("a large swing on many answers is not", () => {
    const run = detail("run", [{ id: "england", answers: 200, failed: 0, reasonable: 40 }]);
    const other = detail("other", [{ id: "england", answers: 200, failed: 0, reasonable: 160 }]);
    expect(compareRuns(run, other)!.overlapping).toBe(false);
  });

  test("failed answers are left out of the score on each side", () => {
    const run = detail("run", [{ id: "england", answers: 100, failed: 6, reasonable: 23 }]);
    const other = detail("other", [{ id: "england", answers: 30, failed: 0, reasonable: 14 }]);
    expect(compareRuns(run, other)!.here.score).toBe(23 / 94);
  });

  test("a side with no usable answer has no score and no verdict", () => {
    const run = detail("run", [{ id: "england", answers: 2, failed: 2, reasonable: 0 }]);
    const other = detail("other", [{ id: "england", answers: 30, failed: 0, reasonable: 14 }]);
    const comparison = compareRuns(run, other)!;
    expect(comparison.here.score).toBeNull();
    expect(comparison.overlapping).toBeNull();
  });
});
