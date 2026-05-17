import { describe, test, expect } from "vitest";
import { parseDsvg } from "./dsvgParser";
import { TOY_DSVG } from "./fixtures";

describe("parseDsvg", () => {
  test("extracts the viewBox", () => {
    expect(parseDsvg(TOY_DSVG).viewBox).toEqual({
      minX: 0,
      minY: 0,
      width: 200,
      height: 100,
    });
  });

  test("maps province ids to their path data", () => {
    const { provincePaths } = parseDsvg(TOY_DSVG);
    expect([...provincePaths.keys()]).toEqual(["alpha", "beta", "gamma"]);
    expect(provincePaths.get("alpha")).toBe("M0 0 L10 0 L10 10 Z");
  });

  test("keeps named coasts separate from provinces", () => {
    const { provincePaths, namedCoastPaths } = parseDsvg(TOY_DSVG);
    expect(provincePaths.has("alpha/nc")).toBe(false);
    expect(namedCoastPaths.get("alpha/nc")).toBe("M0 0 L5 0 L5 5 Z");
  });

  test("maps unit positions for provinces and named coasts", () => {
    const { unitPositions } = parseDsvg(TOY_DSVG);
    expect(unitPositions.get("beta")).toEqual({ x: 25, y: 5 });
    expect(unitPositions.get("alpha/nc")).toEqual({ x: 2, y: 3 });
  });

  test("maps supply-center positions", () => {
    const { supplyCenters } = parseDsvg(TOY_DSVG);
    expect([...supplyCenters.keys()]).toEqual(["alpha", "gamma"]);
    expect(supplyCenters.get("gamma")).toEqual({ x: 45, y: 8 });
  });

  test("exposes the visible layers as inert markup", () => {
    const parsed = parseDsvg(TOY_DSVG);
    expect(parsed.background).toContain("<rect");
    expect(parsed.borders).toContain("<path");
    expect(parsed.foreground).toContain("<circle");
    expect(parsed.provinceNames).toContain("<text");
    expect(parsed.defs).toContain("<style");
  });

  test("returns empty maps when the position layers are absent", () => {
    const withoutPositions = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">
      <g id="background"></g>
      <g id="provinces" style="display:none"><path id="alpha" d="M0 0 Z"/></g>
      <g id="named-coasts" style="display:none"></g>
      <g id="province-names"></g>
      <g id="borders"></g>
      <g id="foreground"></g>
    </svg>`;
    const parsed = parseDsvg(withoutPositions);
    expect(parsed.unitPositions.size).toBe(0);
    expect(parsed.supplyCenters.size).toBe(0);
    expect(parsed.provincePaths.get("alpha")).toBe("M0 0 Z");
  });

  test("throws on malformed XML", () => {
    expect(() =>
      parseDsvg('<svg xmlns="http://www.w3.org/2000/svg"><g></svg>')
    ).toThrow();
  });

  test("throws when the viewBox is missing", () => {
    expect(() =>
      parseDsvg('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
    ).toThrow(/viewBox/);
  });
});
