import { describe, expect, test } from "vitest";
import type { GamePhase, Phase } from "./api";
import {
  centreTimeline,
  firstPhaseOf,
  formatBand,
  mergeNotes,
  OVERALL,
  phaseKey,
  phaseLabel,
  referenceBand,
  stitchNotes,
} from "./games";

const gamePhase = (season: string, year: number, type: string, supply_centers = [] as GamePhase["supply_centers"]) => {
  const phase: Phase = { season, year, type };
  return { key: phaseKey(phase), phase, units: [], supply_centers, dislodged: [], orders: [], answer: null };
};

const PHASES: GamePhase[] = [
  gamePhase("Spring", 1901, "Movement", [{ nation: "England", province: "lon" }]),
  gamePhase("Fall", 1901, "Movement"),
  gamePhase("Fall", 1901, "Adjustment"),
  gamePhase("Spring", 1902, "Movement", [
    { nation: "England", province: "lon" },
    { nation: "England", province: "nwy" },
    { nation: "France", province: "par" },
  ]),
  gamePhase("Fall", 1902, "Movement"),
];

describe("phaseKey", () => {
  test("names the year, season and type", () => {
    expect(phaseKey({ season: "Fall", year: 1902, type: "Movement" })).toBe("1902-Fall-Movement");
  });

  test("labels a phase season first", () => {
    expect(phaseLabel({ season: "Fall", year: 1902, type: "Movement" })).toBe("Fall 1902 Movement");
  });
});

describe("stitchNotes", () => {
  test("puts the overall note first and the phase notes in game order", () => {
    const notes = stitchNotes(
      { overall: "Too passive.", phases: { "1902-Fall-Movement": "Left Norway open.", "1901-Fall-Movement": "Good." } },
      PHASES
    );
    expect(notes.map(note => `${note.heading} ${note.text}`)).toEqual([
      "Overall: Too passive.",
      "Fall 1901 Movement: Good.",
      "Fall 1902 Movement: Left Norway open.",
    ]);
  });

  test("leaves out empty notes", () => {
    const notes = stitchNotes({ overall: "  ", phases: { "1901-Fall-Movement": "", "1902-Fall-Movement": "x" } }, PHASES);
    expect(notes.map(note => note.key)).toEqual(["1902-Fall-Movement"]);
  });

  test("unsaved drafts replace the saved notes they edit", () => {
    const merged = mergeNotes(
      { overall: "old", phases: { "1901-Fall-Movement": "kept", "1902-Fall-Movement": "old" } },
      { [OVERALL]: "new", "1902-Fall-Movement": "" }
    );
    expect(merged).toEqual({ overall: "new", phases: { "1901-Fall-Movement": "kept", "1902-Fall-Movement": "" } });
  });
});

describe("centreTimeline", () => {
  test("counts every nation's centres at the start of each year and at the end", () => {
    const timeline = centreTimeline(PHASES, { England: 3, France: 1 });
    expect(timeline).toEqual([
      { label: "1901", year: 1901, centres: { England: 1, France: 0 } },
      { label: "1902", year: 1902, centres: { England: 2, France: 1 } },
      { label: "End", year: null, centres: { England: 3, France: 1 } },
    ]);
  });

  test("a year jumps to its first phase and the end to the last phase", () => {
    expect(firstPhaseOf(PHASES, 1902)?.key).toBe("1902-Spring-Movement");
    expect(firstPhaseOf(PHASES, null)?.key).toBe("1902-Fall-Movement");
  });
});

describe("referenceBand", () => {
  test("gives the mean centres and share with an interval for the mean share", () => {
    const band = referenceBand({
      games: [
        { seed: 0, centres: 4, share: 10 },
        { seed: 1, centres: 6, share: 20 },
      ],
    })!;
    expect([band.centres, band.share, band.games]).toEqual([5, 15, 2]);
    expect(band.interval!.low).toBeCloseTo(15 - 1.96 * 5);
    expect(formatBand(band)).toBe("5 centres · 15.0% (5.2–24.8%)");
  });

  test("a missing reference file has no band", () => {
    expect(referenceBand(null)).toBeNull();
    expect(formatBand(null)).toBe("no reference");
  });
});
