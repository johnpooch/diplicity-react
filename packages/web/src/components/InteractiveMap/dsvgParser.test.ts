import { describe, test, expect } from "vitest";
import { parseDsvg } from "./dsvgParser";
import { TOY_DSVG } from "./fixtures";

describe("parseDsvg", () => {
  test("extracts the viewBox", () => {
    expect(parseDsvg(TOY_DSVG).viewBox).toEqual({
      minX: 0,
      minY: 0,
      width: 600,
      height: 400,
    });
  });

  test("maps province ids to their path data", () => {
    const { provincePaths } = parseDsvg(TOY_DSVG);
    expect([...provincePaths.keys()]).toEqual(["alpha", "beta", "gamma"]);
    expect(provincePaths.get("alpha")).toBe(
      "M105 70 L210 65 L235 130 L200 200 L110 205 L90 135 Z"
    );
  });

  test("keeps named coasts separate from provinces", () => {
    const { provincePaths, namedCoastPaths } = parseDsvg(TOY_DSVG);
    expect(provincePaths.has("alpha/nc")).toBe(false);
    expect(namedCoastPaths.get("alpha/nc")).toBe("M230 95 L280 90 L275 140 Z");
  });

  test("maps unit positions for provinces and named coasts", () => {
    const { unitPositions } = parseDsvg(TOY_DSVG);
    expect(unitPositions.get("beta")).toEqual({ x: 300, y: 300 });
    expect(unitPositions.get("alpha/nc")).toEqual({ x: 210, y: 110 });
  });

  test("maps supply-center positions", () => {
    const { supplyCenters } = parseDsvg(TOY_DSVG);
    expect([...supplyCenters.keys()]).toEqual(["alpha", "gamma"]);
    expect(supplyCenters.get("gamma")).toEqual({ x: 490, y: 175 });
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

  test("captures root fill when present", () => {
    const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10" fill="none">
      <g id="background"></g>
      <g id="provinces" style="display:none"></g>
      <g id="named-coasts" style="display:none"></g>
      <g id="unit-positions" style="display:none"></g>
      <g id="supply-centers" style="display:none"></g>
      <g id="province-names"></g>
      <g id="borders"></g>
      <g id="foreground"></g>
    </svg>`;
    expect(parseDsvg(svg).rootFill).toBe("none");
  });

  test("rootFill is null when root has no fill attribute", () => {
    expect(parseDsvg(TOY_DSVG).rootFill).toBeNull();
  });
});
