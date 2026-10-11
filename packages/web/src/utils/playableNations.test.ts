import { describe, it, expect } from "vitest";
import { countPlayableNations } from "./playableNations";

describe("countPlayableNations", () => {
  it("excludes non-playable nations", () => {
    expect(
      countPlayableNations([
        { nonPlayable: false },
        { nonPlayable: true },
        { nonPlayable: false },
      ])
    ).toBe(2);
  });

  it("returns zero for no nations", () => {
    expect(countPlayableNations([])).toBe(0);
  });
});
