import { describe, test, expect } from "vitest";
import type {
  Nation,
  Order,
  PhaseRetrieve,
  Province,
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
            dislodgedBy: null,
          },
          {
            type: "Fleet",
            nation: nations[1],
            province: province("bre"),
            dislodged: true,
            dislodgedBy: null,
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
            dislodgedBy: null,
          },
          {
            type: "Fleet",
            nation: nations[1],
            province: province("bre"),
            dislodged: false,
            dislodgedBy: null,
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
});
