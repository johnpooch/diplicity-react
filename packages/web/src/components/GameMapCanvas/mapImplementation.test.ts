import { describe, it, expect, beforeEach, afterEach } from "vitest";
import { resolveMapImplementation } from "./mapImplementation";

const setSearch = (search: string): void => {
  window.history.replaceState({}, "", `/${search}`);
};

describe("resolveMapImplementation", () => {
  beforeEach(() => {
    setSearch("");
    window.localStorage.clear();
  });

  afterEach(() => {
    setSearch("");
    window.localStorage.clear();
  });

  it("defaults to the svg implementation", () => {
    expect(resolveMapImplementation()).toBe("svg");
  });

  it("selects leaflet via the map query param", () => {
    setSearch("?map=leaflet");
    expect(resolveMapImplementation()).toBe("leaflet");
  });

  it("accepts canvas as an alias for leaflet", () => {
    setSearch("?map=canvas");
    expect(resolveMapImplementation()).toBe("leaflet");
  });

  it("lets an explicit svg query param override stored preference", () => {
    window.localStorage.setItem("map:impl", "leaflet");
    setSearch("?map=svg");
    expect(resolveMapImplementation()).toBe("svg");
  });

  it("falls back to the stored preference when no query param is present", () => {
    window.localStorage.setItem("map:impl", "leaflet");
    expect(resolveMapImplementation()).toBe("leaflet");
  });
});
