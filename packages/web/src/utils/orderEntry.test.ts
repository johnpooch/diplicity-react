import { describe, it, expect } from "vitest";
import { canEnterOrdersForPhase } from "./orderEntry";

const activeGame = { status: "active", currentPhaseId: 2 };
const activePhase = { status: "active" } as const;

describe("canEnterOrdersForPhase", () => {
  it("allows order entry on the game's current active phase", () => {
    expect(canEnterOrdersForPhase(activeGame, activePhase, 2)).toBe(true);
  });

  it("disallows order entry on a historical phase", () => {
    expect(canEnterOrdersForPhase(activeGame, { status: "completed" }, 1)).toBe(false);
  });

  it("disallows order entry on a selected phase that is no longer current", () => {
    expect(canEnterOrdersForPhase(activeGame, activePhase, 1)).toBe(false);
  });

  it("disallows order entry while the phase is processing", () => {
    expect(canEnterOrdersForPhase(activeGame, { status: "processing" }, 2)).toBe(false);
  });

  it("disallows order entry once the game is completed", () => {
    expect(
      canEnterOrdersForPhase({ ...activeGame, status: "completed" }, activePhase, 2)
    ).toBe(false);
  });
});
