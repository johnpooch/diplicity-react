import { describe, test, expect } from "vitest";
import type {
  Nation,
  Order,
  PhaseRetrieve,
  Province,
  VariantProvince,
} from "../../api/generated/endpoints";
import { toRenderState } from "./toRenderState";

const province = (id: string, parentId: string | null = null): Province => ({
  id,
  name: id,
  type: "land",
  supplyCenter: false,
  parentId,
  namedCoastIds: [],
});

const variantProvince = (
  id: string,
  opts: {
    parentId?: string | null;
    type?: string;
    supplyCenter?: boolean;
    adjacencies?: string[];
  } = {}
): VariantProvince => ({
  id,
  parentId: opts.parentId ?? null,
  type: opts.type ?? "land",
  supplyCenter: opts.supplyCenter ?? false,
  adjacencies: opts.adjacencies ?? [],
});

const nations: Nation[] = [
  { nationId: "england", name: "England", color: "#2196F3", flagUrl: null },
  { nationId: "france", name: "France", color: "#80DEEA", flagUrl: null },
];

const variant = { nations };

const emptyPhase: PhaseRetrieve = {
  id: 1,
  ordinal: 1,
  season: "Spring",
  year: 1901,
  name: "Spring 1901 Movement",
  type: "Movement",
  remainingTime: 0,
  scheduledResolution: "1901-01-01T00:00:00Z",
  status: "active",
  units: [],
  supplyCenters: [],
  previousPhaseId: null,
  nextPhaseId: null,
};

const baseOrder: Order = {
  source: province("lon"),
  sourceCoast: null,
  target: province("nth"),
  aux: province("lon"),
  namedCoast: province("lon"),
  resolution: { status: "", by: null },
  options: [],
  orderType: "Hold",
  unitType: "Army",
  nation: nations[0],
  complete: null,
  step: null,
  title: null,
  summary: null,
};

describe("toRenderState", () => {
  test("builds nationColors from variant.nations", () => {
    const state = toRenderState(variant, emptyPhase, [], [], []);
    expect(state.nationColors).toEqual({
      England: "#2196F3",
      France: "#80DEEA",
    });
  });

  test("flattens units to province id + nation name", () => {
    const state = toRenderState(
      variant,
      {
        ...emptyPhase,
        units: [
          {
            type: "Army",
            nation: nations[0],
            province: province("lon"),
            dislodged: false,
          },
          {
            type: "Fleet",
            nation: nations[1],
            province: province("bre"),
            dislodged: true,
          },
        ],
      },
      [],
      [],
      []
    );

    expect(state.units).toEqual([
      { province: "lon", nation: "England", type: "Army", dislodged: false, civilDisorder: false },
      { province: "bre", nation: "France", type: "Fleet", dislodged: true, civilDisorder: false },
    ]);
  });

  test("marks units of civil disorder nations", () => {
    const state = toRenderState(
      variant,
      {
        ...emptyPhase,
        units: [
          {
            type: "Army",
            nation: nations[0],
            province: province("lon"),
            dislodged: false,
          },
          {
            type: "Fleet",
            nation: nations[1],
            province: province("bre"),
            dislodged: false,
          },
        ],
      },
      [],
      [],
      [],
      ["England"]
    );

    expect(state.units?.[0].civilDisorder).toBe(true);
    expect(state.units?.[1].civilDisorder).toBe(false);
  });

  test("flattens supplyCenters to province id + nation name", () => {
    const state = toRenderState(
      variant,
      {
        ...emptyPhase,
        supplyCenters: [
          { province: province("lon"), nation: nations[0] },
          { province: province("par"), nation: nations[1] },
        ],
      },
      [],
      [],
      []
    );

    expect(state.supplyCenters).toEqual([
      { province: "lon", nation: "England" },
      { province: "par", nation: "France" },
    ]);
  });

  test("passes selected and highlighted through", () => {
    const state = toRenderState(
      variant,
      emptyPhase,
      [],
      ["lon"],
      ["par", "bre"]
    );
    expect(state.selected).toEqual(["lon"]);
    expect(state.highlighted).toEqual(["par", "bre"]);
  });

  describe("orders", () => {
    test("marks failed when resolution.status is not Succeeded", () => {
      const state = toRenderState(
        variant,
        emptyPhase,
        [{ ...baseOrder, resolution: { status: "Bounce", by: null } }],
        [],
        []
      );
      expect(state.orders?.[0].failed).toBe(true);
    });

    test("does not mark failed when resolution.status is Succeeded", () => {
      const state = toRenderState(
        variant,
        emptyPhase,
        [{ ...baseOrder, resolution: { status: "Succeeded", by: null } }],
        [],
        []
      );
      expect(state.orders?.[0].failed).toBe(false);
    });

    test("does not mark failed when resolution is null", () => {
      const state = toRenderState(
        variant,
        emptyPhase,
        [{ ...baseOrder, resolution: null as unknown as Order["resolution"] }],
        [],
        []
      );
      expect(state.orders?.[0].failed).toBe(false);
    });

    test("Move uses sourceCoast for source and namedCoast for target", () => {
      const state = toRenderState(
        variant,
        emptyPhase,
        [
          {
            ...baseOrder,
            orderType: "Move",
            source: province("stp"),
            sourceCoast: province("stp/nc", "stp"),
            target: province("bot"),
            namedCoast: province("stp/sc", "stp"),
          },
        ],
        [],
        []
      );
      expect(state.orders?.[0]).toMatchObject({
        type: "Move",
        source: "stp/nc",
        target: "stp/sc",
      });
    });

    test("MoveViaConvoy uses sourceCoast for source and namedCoast for target", () => {
      const state = toRenderState(
        variant,
        emptyPhase,
        [
          {
            ...baseOrder,
            orderType: "MoveViaConvoy",
            source: province("lon"),
            sourceCoast: province("lon/sc", "lon"),
            target: province("spa"),
            namedCoast: province("spa/nc", "spa"),
          },
        ],
        [],
        []
      );
      expect(state.orders?.[0]).toMatchObject({
        source: "lon/sc",
        target: "spa/nc",
      });
    });

    test("Build uses namedCoast for source (the new unit's location)", () => {
      const state = toRenderState(
        variant,
        emptyPhase,
        [
          {
            ...baseOrder,
            orderType: "Build",
            source: province("stp"),
            namedCoast: province("stp/sc", "stp"),
            unitType: "Fleet",
          },
        ],
        [],
        []
      );
      expect(state.orders?.[0]).toMatchObject({
        type: "Build",
        source: "stp/sc",
        unitType: "Fleet",
      });
    });

    test("Support ignores sourceCoast and namedCoast", () => {
      const state = toRenderState(
        variant,
        emptyPhase,
        [
          {
            ...baseOrder,
            orderType: "Support",
            source: province("nth"),
            sourceCoast: province("nth/x", "nth"),
            target: province("bel"),
            aux: province("hol"),
            namedCoast: province("bel/x", "bel"),
          },
        ],
        [],
        []
      );
      expect(state.orders?.[0]).toMatchObject({
        type: "Support",
        source: "nth",
        target: "bel",
        aux: "hol",
      });
    });

    test("Convoy ignores sourceCoast and namedCoast", () => {
      const state = toRenderState(
        variant,
        emptyPhase,
        [
          {
            ...baseOrder,
            orderType: "Convoy",
            source: province("eng"),
            sourceCoast: province("eng/x", "eng"),
            target: province("bre"),
            aux: province("lon"),
            namedCoast: province("bre/x", "bre"),
          },
        ],
        [],
        []
      );
      expect(state.orders?.[0]).toMatchObject({
        type: "Convoy",
        source: "eng",
        target: "bre",
        aux: "lon",
      });
    });

    test("Hold and Disband fall back to source.id without coast resolution", () => {
      const state = toRenderState(
        variant,
        emptyPhase,
        [
          {
            ...baseOrder,
            orderType: "Hold",
            source: province("lon"),
            sourceCoast: null,
          },
          {
            ...baseOrder,
            orderType: "Disband",
            source: province("ven"),
            sourceCoast: null,
          },
        ],
        [],
        []
      );
      expect(state.orders?.[0].source).toBe("lon");
      expect(state.orders?.[1].source).toBe("ven");
    });

    test("Hold/Disband use sourceCoast when present (unit on a named coast)", () => {
      const state = toRenderState(
        variant,
        emptyPhase,
        [
          {
            ...baseOrder,
            orderType: "Hold",
            source: province("stp"),
            sourceCoast: province("stp/nc", "stp"),
          },
        ],
        [],
        []
      );
      expect(state.orders?.[0].source).toBe("stp/nc");
    });

    test("omits aux when order has no aux", () => {
      const state = toRenderState(
        variant,
        emptyPhase,
        [
          {
            ...baseOrder,
            orderType: "Hold",
            aux: null as unknown as Order["aux"],
          },
        ],
        [],
        []
      );
      expect(state.orders?.[0].aux).toBeUndefined();
    });
  });

  describe("nonScProvinceColors", () => {
    test("returns empty object when no provinces provided", () => {
      const state = toRenderState(variant, emptyPhase, [], [], []);
      expect(state.nonScProvinceColors).toEqual({});
    });

    test("colors a non-SC province when all adjacent SCs belong to the same nation", () => {
      // yor is adjacent to lon (England SC) and edi (England SC)
      const provinces = [
        variantProvince("lon", { supplyCenter: true }),
        variantProvince("edi", { supplyCenter: true }),
        variantProvince("yor", { type: "coastal", adjacencies: ["lon", "edi"] }),
      ];
      const state = toRenderState(
        { ...variant, provinces },
        {
          ...emptyPhase,
          supplyCenters: [
            { province: province("lon"), nation: nations[0] },
            { province: province("edi"), nation: nations[0] },
          ],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["yor"]).toBe("#2196F3");
    });

    test("does not color a non-SC province when adjacent SCs belong to different nations", () => {
      // bur is adjacent to par (France SC) and mun (Germany SC)
      const provinces = [
        variantProvince("par", { supplyCenter: true }),
        variantProvince("mun", { supplyCenter: true }),
        variantProvince("bur", { adjacencies: ["par", "mun"] }),
      ];
      const state = toRenderState(
        {
          nations: [
            ...nations,
            { nationId: "germany", name: "Germany", color: "#90A4AE", flagUrl: null },
          ],
          provinces,
        },
        {
          ...emptyPhase,
          supplyCenters: [
            { province: province("par"), nation: nations[1] },
            { province: province("mun"), nation: { nationId: "germany", name: "Germany", color: "#90A4AE", flagUrl: null } },
          ],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["bur"]).toBeUndefined();
    });

    test("does not color a non-SC province when any adjacent SC is neutral/unowned", () => {
      // gas is adjacent to par (France SC) and spa (neutral SC)
      const provinces = [
        variantProvince("par", { supplyCenter: true }),
        variantProvince("spa", { supplyCenter: true }),
        variantProvince("gas", { type: "coastal", adjacencies: ["par", "spa"] }),
      ];
      const state = toRenderState(
        { ...variant, provinces },
        {
          ...emptyPhase,
          supplyCenters: [
            { province: province("par"), nation: nations[1] },
            // spa is not in supplyCenters → neutral/unowned
          ],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["gas"]).toBeUndefined();
    });

    test("does not color a non-SC province with no adjacent SCs", () => {
      const provinces = [
        variantProvince("sea1", { type: "sea", supplyCenter: false }),
        variantProvince("land1", { adjacencies: ["sea1"] }),
      ];
      const state = toRenderState(
        { ...variant, provinces },
        emptyPhase,
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["land1"]).toBeUndefined();
    });

    test("does not color SC provinces", () => {
      const provinces = [
        variantProvince("lon", { supplyCenter: true, adjacencies: [] }),
      ];
      const state = toRenderState(
        { ...variant, provinces },
        {
          ...emptyPhase,
          supplyCenters: [{ province: province("lon"), nation: nations[0] }],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["lon"]).toBeUndefined();
    });

    test("does not color sea provinces", () => {
      const provinces = [
        variantProvince("lon", { supplyCenter: true }),
        variantProvince("nth", { type: "sea", adjacencies: ["lon"] }),
      ];
      const state = toRenderState(
        { ...variant, provinces },
        {
          ...emptyPhase,
          supplyCenters: [{ province: province("lon"), nation: nations[0] }],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["nth"]).toBeUndefined();
    });

    test("resolves named coast adjacencies to the parent SC", () => {
      // gas is adjacent to spa (SC) via named coast spa/nc
      const provinces = [
        variantProvince("spa", { supplyCenter: true }),
        variantProvince("spa/nc", { parentId: "spa", type: "named_coast" }),
        variantProvince("gas", { type: "coastal", adjacencies: ["spa/nc"] }),
      ];
      const state = toRenderState(
        { ...variant, provinces },
        {
          ...emptyPhase,
          supplyCenters: [{ province: province("spa"), nation: nations[1] }],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["gas"]).toBe("#80DEEA");
    });

    test("deduplicates when both parent SC and named coast appear in adjacency list", () => {
      // province adjacent to both spa and spa/nc — should count as one SC
      const provinces = [
        variantProvince("spa", { supplyCenter: true }),
        variantProvince("spa/nc", { parentId: "spa", type: "named_coast" }),
        variantProvince("test", { type: "coastal", adjacencies: ["spa", "spa/nc"] }),
      ];
      const state = toRenderState(
        { ...variant, provinces },
        {
          ...emptyPhase,
          supplyCenters: [{ province: province("spa"), nation: nations[1] }],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["test"]).toBe("#80DEEA");
    });
  });

  describe("dominanceRules", () => {
    const turkey = { nationId: "turkey", name: "Turkey", color: "#FFC107", flagUrl: null };
    const russia = { nationId: "russia", name: "Russia", color: "#F5F5F5", flagUrl: null };

    const armProvinces = [
      variantProvince("ank", { supplyCenter: true }),
      variantProvince("sev", { supplyCenter: true }),
      variantProvince("smy", { supplyCenter: true }),
      variantProvince("arm", { type: "coastal", adjacencies: ["ank", "sev", "smy"] }),
    ];

    const armRule = {
      province: "arm",
      nation: "turkey",
      dependencies: [
        { province: "ank", nation: "turkey" },
        { province: "sev", nation: "russia" },
        { province: "smy", nation: "turkey" },
      ],
    };

    test("colors a province using a dominance rule when all dependencies match", () => {
      const state = toRenderState(
        { nations: [turkey, russia], provinces: armProvinces, dominanceRules: [armRule] },
        {
          ...emptyPhase,
          supplyCenters: [
            { province: province("ank"), nation: turkey },
            { province: province("sev"), nation: russia },
            { province: province("smy"), nation: turkey },
          ],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["arm"]).toBe("#FFC107");
    });

    test("falls back to default logic when a dependency does not match", () => {
      // sev is taken by Turkey instead of Russia — rule fails
      // default logic: ank=Turkey, sev=Turkey, smy=Turkey → all Turkey → colors Turkey
      const state = toRenderState(
        { nations: [turkey, russia], provinces: armProvinces, dominanceRules: [armRule] },
        {
          ...emptyPhase,
          supplyCenters: [
            { province: province("ank"), nation: turkey },
            { province: province("sev"), nation: turkey },
            { province: province("smy"), nation: turkey },
          ],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["arm"]).toBe("#FFC107");
    });

    test("falls back to no color when rule fails and default also fails", () => {
      // sev is taken by Russia (rule requires Turkey for sev) and ank=Turkey, smy=Turkey
      // But wait — the rule requires sev=Russia, so this should MATCH the rule
      // Let's test the case where the rule fails AND default fails:
      // sev=Russia (breaks rule which needs sev=Russia? no that's correct)
      // Let me set up: rule requires sev=Russia but sev=neutral → rule fails
      // default: ank=Turkey, sev=neutral (fails) → no default color
      const state = toRenderState(
        { nations: [turkey, russia], provinces: armProvinces, dominanceRules: [armRule] },
        {
          ...emptyPhase,
          supplyCenters: [
            { province: province("ank"), nation: turkey },
            // sev is neutral (not in supply centers)
            { province: province("smy"), nation: turkey },
          ],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["arm"]).toBeUndefined();
    });

    test("matches 'Empty' dependency when the SC is unowned", () => {
      // ukr rule: mos=russia, rum=Empty, sev=russia, war=russia
      const ukrProvinces = [
        variantProvince("mos", { supplyCenter: true }),
        variantProvince("rum", { supplyCenter: true }),
        variantProvince("sev", { supplyCenter: true }),
        variantProvince("war", { supplyCenter: true }),
        variantProvince("ukr", { adjacencies: ["mos", "rum", "sev", "war"] }),
      ];
      const ukrRule = {
        province: "ukr",
        nation: "russia",
        dependencies: [
          { province: "mos", nation: "russia" },
          { province: "rum", nation: "Empty" },
          { province: "sev", nation: "russia" },
          { province: "war", nation: "russia" },
        ],
      };
      const state = toRenderState(
        { nations: [turkey, russia], provinces: ukrProvinces, dominanceRules: [ukrRule] },
        {
          ...emptyPhase,
          supplyCenters: [
            { province: province("mos"), nation: russia },
            // rum is neutral — not in supply centers
            { province: province("sev"), nation: russia },
            { province: province("war"), nation: russia },
          ],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["ukr"]).toBe("#F5F5F5");
    });

    test("fails 'Empty' dependency when the SC is owned", () => {
      const ukrProvinces = [
        variantProvince("mos", { supplyCenter: true }),
        variantProvince("rum", { supplyCenter: true }),
        variantProvince("sev", { supplyCenter: true }),
        variantProvince("war", { supplyCenter: true }),
        variantProvince("ukr", { adjacencies: ["mos", "rum", "sev", "war"] }),
      ];
      const ukrRule = {
        province: "ukr",
        nation: "russia",
        dependencies: [
          { province: "mos", nation: "russia" },
          { province: "rum", nation: "Empty" },
          { province: "sev", nation: "russia" },
          { province: "war", nation: "russia" },
        ],
      };
      // rum is now owned by Austria → Empty dependency fails → rule falls back to default
      // default: mos=Russia, rum=Austria, sev=Russia, war=Russia → not all same → no color
      const austria = { nationId: "austria", name: "Austria", color: "#F44336", flagUrl: null };
      const state = toRenderState(
        { nations: [turkey, russia, austria], provinces: ukrProvinces, dominanceRules: [ukrRule] },
        {
          ...emptyPhase,
          supplyCenters: [
            { province: province("mos"), nation: russia },
            { province: province("rum"), nation: austria },
            { province: province("sev"), nation: russia },
            { province: province("war"), nation: russia },
          ],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["ukr"]).toBeUndefined();
    });

    test("treats 'Neutral' the same as 'Empty'", () => {
      const provinces = [
        variantProvince("ank", { supplyCenter: true }),
        variantProvince("test", { adjacencies: ["ank"] }),
      ];
      const rule = {
        province: "test",
        nation: "turkey",
        dependencies: [{ province: "ank", nation: "Neutral" }],
      };
      const state = toRenderState(
        { nations: [turkey, russia], provinces, dominanceRules: [rule] },
        { ...emptyPhase, supplyCenters: [] }, // ank unowned
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["test"]).toBe("#FFC107");
    });

    test("ignores a dependency with an unrecognized nation ID (falls back to default)", () => {
      const rule = {
        province: "arm",
        nation: "turkey",
        dependencies: [{ province: "ank", nation: "unknown-nation" }],
      };
      // unknown-nation is not a nation ID and not Empty/Neutral → fails
      // default: ank=Turkey, sev+smy neutral → no default color
      const state = toRenderState(
        { nations: [turkey, russia], provinces: armProvinces, dominanceRules: [rule] },
        {
          ...emptyPhase,
          supplyCenters: [{ province: province("ank"), nation: turkey }],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["arm"]).toBeUndefined();
    });

    test("works correctly with no dominance rules (empty array)", () => {
      const state = toRenderState(
        { nations: [turkey, russia], provinces: armProvinces, dominanceRules: [] },
        {
          ...emptyPhase,
          supplyCenters: [
            { province: province("ank"), nation: turkey },
            { province: province("sev"), nation: turkey },
            { province: province("smy"), nation: turkey },
          ],
        },
        [],
        [],
        []
      );
      expect(state.nonScProvinceColors?.["arm"]).toBe("#FFC107");
    });
  });
});
