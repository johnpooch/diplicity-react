import { describe, it, expect } from "vitest";
import { modeToBackendFields } from "./CreateGame";

describe("modeToBackendFields", () => {
  it("maps standard mode to full press with named players", () => {
    expect(modeToBackendFields("standard")).toEqual({
      anonymous: false,
      pressType: "full_press",
    });
  });

  it("maps gunboat mode to no press with anonymous players", () => {
    expect(modeToBackendFields("gunboat")).toEqual({
      anonymous: true,
      pressType: "no_press",
    });
  });
});
