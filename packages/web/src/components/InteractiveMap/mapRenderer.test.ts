import { describe, test, expect } from "vitest";
import { DiplicityMap, type RenderState } from "./mapRenderer";
import { TOY_DSVG, CONVOY_DSVG } from "./fixtures";

const CONVOY_SCENE: RenderState = {
  nationColors: { England: "#1b4f9c" },
  units: [
    { province: "alpha", nation: "England", type: "Army" },
    { province: "beta", nation: "England", type: "Fleet" },
  ],
  orders: [
    {
      type: "MoveViaConvoy",
      nation: "England",
      source: "alpha",
      target: "gamma",
    },
    {
      type: "Convoy",
      nation: "England",
      source: "beta",
      aux: "alpha",
      target: "gamma",
    },
  ],
};

const TOY_STATE: RenderState = {
  nationColors: { England: "#1b4f9c", France: "#3b9c3b" },
  supplyCenters: [
    { province: "alpha", nation: "England" },
    { province: "gamma", nation: "France" },
  ],
  units: [
    { province: "alpha", nation: "England", type: "Army" },
    { province: "beta", nation: "France", type: "Fleet", dislodged: true },
  ],
  orders: [
    { type: "Hold", nation: "England", source: "alpha", failed: true },
    { type: "Build", nation: "France", source: "gamma", unitType: "Fleet" },
    { type: "Disband", nation: "France", source: "beta" },
  ],
  selected: ["beta"],
  highlighted: ["gamma"],
};

describe("DiplicityMap static base", () => {
  test("renders an svg root carrying the dSVG viewBox", () => {
    const svg = new DiplicityMap(TOY_DSVG).render();
    expect(svg.startsWith("<svg")).toBe(true);
    expect(svg).toContain('viewBox="0 0 200 100"');
  });

  test("omits the hidden metadata layers from the rendered output", () => {
    const svg = new DiplicityMap(TOY_DSVG).render();
    expect(svg).not.toContain('id="provinces"');
    expect(svg).not.toContain('id="named-coasts"');
    expect(svg).not.toContain('id="unit-positions"');
  });

  test("renders no province fills, units or orders without state", () => {
    const svg = new DiplicityMap(TOY_DSVG).render();
    expect(svg).toBe(new DiplicityMap(TOY_DSVG).render({}));
    expect(svg).not.toContain('id="province-fills"');
    expect(svg).not.toContain('id="units"');
    expect(svg).not.toContain('id="orders"');
  });

  test("matches the committed static base-map artifact", async () => {
    const svg = new DiplicityMap(TOY_DSVG).render();
    await expect(svg).toMatchFileSnapshot("./__artifacts__/toy-base.svg");
  });
});

describe("DiplicityMap province fills", () => {
  test("tints a supply center with its owner's nation colour", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { England: "#1b4f9c" },
      supplyCenters: [{ province: "alpha", nation: "England" }],
    });
    expect(svg).toContain('fill="rgba(27, 79, 156, 0.5)"');
  });

  test("uses the lower opacity for a selected supply center", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { England: "#1b4f9c" },
      supplyCenters: [{ province: "alpha", nation: "England" }],
      selected: ["alpha"],
    });
    expect(svg).toContain("rgba(27, 79, 156, 0.3)");
  });

  test("fills and strokes a selected non-supply-centre province", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({ selected: ["beta"] });
    expect(svg).toContain('fill="rgba(255, 255, 255, 0.8)"');
    expect(svg).toContain('stroke="white"');
  });

  test("draws highlighted provinces with stripes, a pulse and the pattern", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({ highlighted: ["gamma"] });
    expect(svg).toContain('id="highlightedStripes"');
    expect(svg).toContain('fill="url(#highlightedStripes)"');
    expect(svg).toContain("<animate");
  });

  test("omits provinces with nothing to draw", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({ selected: ["beta"] });
    expect(svg).not.toContain('d="M0 0 L10 0 L10 10 Z"');
    expect(svg).toContain('d="M20 0 L30 0 L30 10 Z"');
  });

  test("throws when a supply center's nation has no colour", () => {
    expect(() =>
      new DiplicityMap(TOY_DSVG).render({
        supplyCenters: [{ province: "alpha", nation: "Atlantis" }],
      })
    ).toThrow(/Atlantis/);
  });
});

describe("DiplicityMap supply-center markers", () => {
  test("draws a marker at each supply-center position, even without state", () => {
    const svg = new DiplicityMap(TOY_DSVG).render();
    expect(svg).toContain('id="supply-center-markers"');
    expect(svg).toContain('cx="5" cy="8" r="7"');
    expect(svg).toContain('cx="45" cy="8" r="7"');
  });
});

describe("DiplicityMap units", () => {
  test("draws a unit token at the unit position", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { England: "#1b4f9c" },
      units: [{ province: "alpha", nation: "England", type: "Army" }],
    });
    expect(svg).toContain('id="units"');
    expect(svg).toContain('cx="5" cy="5" r="10" fill="#1b4f9c"');
    expect(svg).toContain(">A</text>");
  });

  test("labels armies A and fleets F", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { France: "#3b9c3b" },
      units: [{ province: "beta", nation: "France", type: "Fleet" }],
    });
    expect(svg).toContain(">F</text>");
  });

  test("offsets a dislodged unit and gives it a retreat flag", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { France: "#3b9c3b" },
      units: [
        { province: "beta", nation: "France", type: "Fleet", dislodged: true },
      ],
    });
    expect(svg).toContain('cx="33" cy="13"');
    expect(svg).toContain("translate(");
  });

  test("renders dislodged units after non-dislodged ones", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { England: "#1b4f9c", France: "#3b9c3b" },
      units: [
        { province: "beta", nation: "France", type: "Fleet", dislodged: true },
        { province: "alpha", nation: "England", type: "Army" },
      ],
    });
    expect(svg.indexOf('cx="5" cy="5"')).toBeLessThan(svg.indexOf('cx="33"'));
  });

  test("throws when a unit's nation has no colour", () => {
    expect(() =>
      new DiplicityMap(TOY_DSVG).render({
        units: [{ province: "alpha", nation: "Atlantis", type: "Army" }],
      })
    ).toThrow(/Atlantis/);
  });
});

describe("DiplicityMap orders", () => {
  test("draws an octagon at a Hold order's source", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      orders: [{ type: "Hold", nation: "England", source: "alpha" }],
    });
    expect(svg).toContain('id="orders"');
    expect(svg).toContain("<polygon");
  });

  test("adds a failure cross to a failed Hold only", () => {
    const failed = new DiplicityMap(TOY_DSVG).render({
      orders: [{ type: "Hold", nation: "England", source: "alpha", failed: true }],
    });
    const succeeded = new DiplicityMap(TOY_DSVG).render({
      orders: [{ type: "Hold", nation: "England", source: "alpha" }],
    });
    expect(failed).toContain('stroke="red"');
    expect(succeeded).not.toContain('stroke="red"');
  });

  test("draws a Build as a ghost unit with a green cross", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { France: "#3b9c3b" },
      orders: [
        { type: "Build", nation: "France", source: "gamma", unitType: "Fleet" },
      ],
    });
    expect(svg).toContain('opacity="0.6"');
    expect(svg).toContain('stroke="green"');
    expect(svg).toContain(">F</text>");
  });

  test("draws a Disband as a red marker", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      orders: [{ type: "Disband", nation: "France", source: "alpha" }],
    });
    expect(svg).toContain('stroke="red"');
  });

  test("dims a unit and suppresses its retreat flag when it is disbanding", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { France: "#3b9c3b" },
      units: [
        { province: "alpha", nation: "France", type: "Army", dislodged: true },
      ],
      orders: [{ type: "Disband", nation: "France", source: "alpha" }],
    });
    expect(svg).toContain('opacity="0.7"');
    expect(svg).not.toContain("scale(1.5)");
  });

  test("draws a Move as a straight arrow", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { England: "#1b4f9c" },
      orders: [
        { type: "Move", nation: "England", source: "alpha", target: "beta" },
      ],
    });
    expect(svg).toContain('id="orders"');
    expect(svg).toContain(" L ");
    expect(svg).not.toContain(" Q ");
  });

  test("curves both arrows of a head-to-head move pair", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { England: "#1b4f9c", France: "#3b9c3b" },
      orders: [
        { type: "Move", nation: "England", source: "alpha", target: "beta" },
        { type: "Move", nation: "France", source: "beta", target: "alpha" },
      ],
    });
    expect((svg.match(/ Q /g) ?? []).length).toBe(4);
  });

  test("adds a failure cross to a failed Move", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { England: "#1b4f9c" },
      orders: [
        {
          type: "Move",
          nation: "England",
          source: "alpha",
          target: "beta",
          failed: true,
        },
      ],
    });
    expect(svg).toContain('stroke="red"');
  });

  test("draws a MoveViaConvoy without a matching Convoy as a straight arrow", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { England: "#1b4f9c" },
      orders: [
        {
          type: "MoveViaConvoy",
          nation: "England",
          source: "alpha",
          target: "gamma",
        },
      ],
    });
    expect(svg).toContain('id="orders"');
    expect(svg).toContain(" L ");
    expect(svg).not.toContain(" Q ");
  });

  test("draws a support-hold as a dashed line and an octagon", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { England: "#1b4f9c" },
      orders: [
        {
          type: "Support",
          nation: "England",
          source: "alpha",
          aux: "beta",
          target: "beta",
        },
      ],
    });
    expect(svg).toContain("<polygon");
    expect(svg).toContain('stroke-dasharray="4 2"');
  });

  test("draws a support-move as a dashed curved arrow", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { England: "#1b4f9c" },
      orders: [
        {
          type: "Support",
          nation: "England",
          source: "alpha",
          aux: "beta",
          target: "gamma",
        },
      ],
    });
    expect(svg).toContain(" C ");
    expect(svg).toContain('stroke-dasharray="4 2"');
  });

  test("adds a failure cross to a failed Support", () => {
    const svg = new DiplicityMap(TOY_DSVG).render({
      nationColors: { England: "#1b4f9c" },
      orders: [
        {
          type: "Support",
          nation: "England",
          source: "alpha",
          aux: "beta",
          target: "gamma",
          failed: true,
        },
      ],
    });
    expect(svg).toContain('stroke="red"');
  });

  test("draws a Convoy as a wavy arrow with a fleet circle", () => {
    const svg = new DiplicityMap(CONVOY_DSVG).render({
      nationColors: { England: "#1b4f9c" },
      orders: [
        {
          type: "Convoy",
          nation: "England",
          source: "beta",
          aux: "alpha",
          target: "gamma",
        },
      ],
    });
    expect(svg).toContain(" C ");
    expect(svg).toContain('r="5"');
  });

  test("upgrades a MoveViaConvoy to a routed B-spline when a Convoy matches", () => {
    const svg = new DiplicityMap(CONVOY_DSVG).render(CONVOY_SCENE);
    expect(svg).toContain(" Q ");
  });

  test("matches the committed convoy artifact", async () => {
    const svg = new DiplicityMap(CONVOY_DSVG).render(CONVOY_SCENE);
    await expect(svg).toMatchFileSnapshot("./__artifacts__/toy-convoy.svg");
  });
});

describe("DiplicityMap layering", () => {
  test("composes the visible layers in z-order", () => {
    const svg = new DiplicityMap(TOY_DSVG).render(TOY_STATE);
    const positions = [
      "background",
      "province-fills",
      "supply-center-markers",
      "province-names",
      "borders",
      "units",
      "orders",
      "foreground",
    ].map((id) => svg.indexOf(`id="${id}"`));
    expect(positions.every((index) => index >= 0)).toBe(true);
    expect(positions).toEqual([...positions].sort((a, b) => a - b));
  });

  test("matches the committed board-state artifact", async () => {
    const svg = new DiplicityMap(TOY_DSVG).render(TOY_STATE);
    await expect(svg).toMatchFileSnapshot("./__artifacts__/toy-board.svg");
  });
});
