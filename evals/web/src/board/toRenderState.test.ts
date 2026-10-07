import { describe, expect, test } from "vitest";
import type { BoardState, OrderDetail, Unit } from "../api";
import { toRenderState } from "./toRenderState";

const order = (source: string, order_type: string, extra: Partial<OrderDetail> = {}): OrderDetail => ({
  source,
  order_type,
  target: null,
  aux: null,
  unit_type: null,
  named_coast: null,
  source_name: source,
  description: order_type,
  ...extra,
});

const board = (units: Unit[] = []): BoardState => ({
  id: "f",
  nation: "France",
  phase: { season: "Spring", year: 1901, type: "Movement" },
  units,
  supply_centers: [],
});

describe("toRenderState", () => {
  test("draws a hold without a target and a move to its named coast", () => {
    const state = toRenderState(board(), [
      order("lon", "Hold", { target: "lon" }),
      order("nwy", "Move", { target: "stp", named_coast: "stp/nc" }),
    ]);
    expect(state.orders).toEqual([
      { type: "Hold", nation: "France", source: "lon" },
      { type: "Move", nation: "France", source: "nwy", target: "stp/nc" },
    ]);
  });

  test("an order from a fleet on a named coast starts at that coast", () => {
    const state = toRenderState(
      board([{ type: "Fleet", nation: "France", province: "bul/sc", dislodged: false }]),
      [order("bul", "Move", { target: "gre" })]
    );
    expect(state.orders?.[0].source).toBe("bul/sc");
  });

  test("a support keeps the supported unit and its destination", () => {
    const state = toRenderState(board(), [order("lon", "Support", { target: "yor", aux: "lvp" })]);
    expect(state.orders).toEqual([
      { type: "Support", nation: "France", source: "lon", target: "yor", aux: "lvp" },
    ]);
  });
});
