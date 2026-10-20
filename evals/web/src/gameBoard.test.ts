import { describe, expect, test } from "vitest";
import type { GameOrder, GamePhase } from "./api";
import { gameRenderState } from "./gameBoard";

const order = (nation: string, source: string, order_type: string, extra: Partial<GameOrder> = {}): GameOrder => ({
  nation,
  id: `${source}:${order_type}`,
  source,
  order_type,
  target: null,
  aux: null,
  unit_type: null,
  named_coast: null,
  source_name: source,
  description: order_type,
  result: "OK",
  ...extra,
});

const phase = (orders: GameOrder[], extra: Partial<GamePhase> = {}): GamePhase => ({
  key: "1901-Spring-Movement",
  phase: { season: "Spring", year: 1901, type: "Movement" },
  units: [
    { type: "Army", nation: "France", province: "par", dislodged: false },
    { type: "Army", nation: "Germany", province: "mun", dislodged: false },
    { type: "Fleet", nation: "Spain", province: "spa/sc", dislodged: false },
  ],
  supply_centers: [{ nation: "France", province: "par" }],
  dislodged: [],
  orders,
  answer: null,
  ...extra,
});

describe("gameRenderState", () => {
  test("draws every nation's orders in that nation's colour", () => {
    const state = gameRenderState(
      phase([order("France", "par", "Move", { target: "bur" }), order("Germany", "mun", "Move", { target: "bur" })])
    );
    expect(state.orders?.map(drawn => [drawn.nation, drawn.source, drawn.target])).toEqual([
      ["France", "par", "bur"],
      ["Germany", "mun", "bur"],
    ]);
    expect(state.nationColors?.France).toBeDefined();
  });

  test("draws an order that did not succeed as failed", () => {
    const state = gameRenderState(
      phase([
        order("France", "par", "Move", { target: "bur", result: "ErrBounce" }),
        order("Germany", "mun", "Hold"),
      ])
    );
    expect(state.orders?.map(drawn => drawn.failed ?? false)).toEqual([true, false]);
  });

  test("marks the units the phase dislodged, including one on a named coast", () => {
    const state = gameRenderState(phase([], { dislodged: ["mun", "spa/sc"] }));
    expect(state.units?.filter(unit => unit.dislodged).map(unit => unit.province)).toEqual(["mun", "spa/sc"]);
  });

  test("keeps the units a retreat phase starts with as dislodged", () => {
    const state = gameRenderState(
      phase([order("Germany", "mun", "Move", { target: "boh" })], {
        units: [
          { type: "Army", nation: "France", province: "mun", dislodged: false },
          { type: "Army", nation: "Germany", province: "mun", dislodged: true },
        ],
      })
    );
    expect(state.units?.map(unit => unit.dislodged)).toEqual([false, true]);
    expect(state.orders?.[0]).toMatchObject({ nation: "Germany", source: "mun", target: "boh" });
  });

  test("an order from a fleet on a named coast starts at that coast", () => {
    const state = gameRenderState(phase([order("Spain", "spa", "Move", { target: "wes" })]));
    expect(state.orders?.[0].source).toBe("spa/sc");
  });
});
