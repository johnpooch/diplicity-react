import { describe, test, expect } from "vitest";
import { DiplicityMap, type RenderState } from "./mapRenderer";
// Vendored copy of the converted classical map (service/variant/data/svg/
// classical.d.svg) with the embedded woff2 font and raster pattern tiles
// stripped. The web package's CI test image is built from packages/web
// alone, so the test cannot reach the backend file; the stripped artwork
// is passthrough irrelevant to the renderer geometry under test.
import CLASSICAL_DSVG from "./classicalMap.dsvg?raw";

const CLASSICAL_SCENE: RenderState = {
  // Nation colours from the classical variant (service/variant/data/classical.json).
  nationColors: {
    Austria: "#F44336",
    England: "#2196F3",
    France: "#80DEEA",
    Germany: "#90A4AE",
    Italy: "#4CAF50",
    Russia: "#F5F5F5",
    Turkey: "#FFC107",
  },
  supplyCenters: [
    { province: "lon", nation: "England" },
    { province: "edi", nation: "England" },
    { province: "lvp", nation: "England" },
    { province: "par", nation: "France" },
    { province: "bre", nation: "France" },
    { province: "mar", nation: "France" },
    { province: "mun", nation: "Germany" },
    { province: "kie", nation: "Germany" },
    { province: "ber", nation: "Germany" },
    { province: "vie", nation: "Austria" },
    { province: "bud", nation: "Austria" },
    { province: "tri", nation: "Austria" },
    { province: "rom", nation: "Italy" },
    { province: "ven", nation: "Italy" },
    { province: "war", nation: "Russia" },
    { province: "sev", nation: "Russia" },
    { province: "mos", nation: "Russia" },
    { province: "con", nation: "Turkey" },
    { province: "smy", nation: "Turkey" },
  ],
  units: [
    { province: "nth", nation: "England", type: "Fleet" },
    { province: "yor", nation: "England", type: "Army" },
    { province: "eng", nation: "England", type: "Fleet" },
    { province: "par", nation: "France", type: "Army" },
    { province: "bur", nation: "France", type: "Army" },
    { province: "bre", nation: "France", type: "Fleet" },
    { province: "mun", nation: "Germany", type: "Army" },
    { province: "ruh", nation: "Germany", type: "Army" },
    { province: "kie", nation: "Germany", type: "Fleet" },
    { province: "vie", nation: "Austria", type: "Army" },
    { province: "bud", nation: "Austria", type: "Army" },
    { province: "tri", nation: "Austria", type: "Fleet" },
    { province: "ven", nation: "Italy", type: "Army" },
    { province: "rom", nation: "Italy", type: "Army" },
    { province: "war", nation: "Russia", type: "Army" },
    { province: "sev", nation: "Russia", type: "Fleet" },
    { province: "mos", nation: "Russia", type: "Army" },
    { province: "con", nation: "Turkey", type: "Army" },
    { province: "smy", nation: "Turkey", type: "Fleet" },
  ],
  orders: [
    { type: "MoveViaConvoy", nation: "England", source: "yor", target: "nwy" },
    { type: "Convoy", nation: "England", source: "nth", aux: "yor", target: "nwy" },
    { type: "Move", nation: "England", source: "eng", target: "iri" },
    { type: "Hold", nation: "France", source: "par" },
    { type: "Move", nation: "France", source: "bur", target: "mun" },
    { type: "Support", nation: "France", source: "bre", aux: "par", target: "par" },
    { type: "Move", nation: "Germany", source: "mun", target: "bur" },
    { type: "Support", nation: "Germany", source: "ruh", aux: "mun", target: "bur" },
    { type: "Hold", nation: "Germany", source: "kie" },
    { type: "Move", nation: "Austria", source: "vie", target: "gal" },
    { type: "Support", nation: "Austria", source: "bud", aux: "vie", target: "gal" },
    { type: "Hold", nation: "Austria", source: "tri", failed: true },
    { type: "Move", nation: "Italy", source: "ven", target: "tyr", failed: true },
    { type: "Move", nation: "Italy", source: "rom", target: "ven" },
    { type: "Move", nation: "Russia", source: "war", target: "sil" },
    { type: "Move", nation: "Russia", source: "sev", target: "bla" },
    { type: "Disband", nation: "Russia", source: "mos" },
    { type: "Hold", nation: "Turkey", source: "con" },
    { type: "Move", nation: "Turkey", source: "smy", target: "aeg" },
    { type: "Build", nation: "France", source: "mar", unitType: "Army" },
  ],
  selected: ["mun"],
  // gal: a plain province; stp: a province that has named coasts;
  // spa/nc: a named coast highlighted on its own.
  highlighted: ["gal", "stp", "spa/nc"],
};

describe("DiplicityMap classical board", () => {
  test("places every unit in the scene on the real map", () => {
    const svg = new DiplicityMap(CLASSICAL_DSVG).render(CLASSICAL_SCENE);
    expect(svg).toContain('id="units"');
    // One token per unit, plus a ghost token for each Build order.
    const builds = CLASSICAL_SCENE.orders!.filter(
      (order) => order.type === "Build"
    ).length;
    expect((svg.match(/<text [^>]*>[AF]<\/text>/g) ?? []).length).toBe(
      CLASSICAL_SCENE.units!.length + builds
    );
  });

  test("draws every order type", () => {
    const svg = new DiplicityMap(CLASSICAL_DSVG).render(CLASSICAL_SCENE);
    expect(svg).toContain('id="orders"');
    expect(svg).toContain("<polygon"); // Hold octagons
    expect(svg).toContain(" Q "); // head-to-head bur<->mun curves
    expect(svg).toContain('stroke-dasharray="4 2"'); // support arrows
    expect(svg).toContain('stroke="red"'); // failed orders + disband
  });

  test("matches the committed classical board artifact", async () => {
    const svg = new DiplicityMap(CLASSICAL_DSVG).render(CLASSICAL_SCENE);
    await expect(svg).toMatchFileSnapshot("./__artifacts__/classical-board.svg");
  });
});
