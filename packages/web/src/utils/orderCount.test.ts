import { describe, it, expect } from "vitest";
import type { Order, PhaseState, Province } from "../api/generated/endpoints";
import { countOrders } from "./orderCount";

const province = (id: string) => ({ id }) as unknown as Province;

const phaseState = (overrides: Partial<PhaseState> = {}) =>
  ({
    member: { isCurrentUser: true },
    maxOrders: null,
    orderableProvinces: [province("lon"), province("edi"), province("lvp")],
    ...overrides,
  }) as PhaseState;

const order = (sourceId: string) =>
  ({ source: province(sourceId) }) as unknown as Order;

describe("countOrders", () => {
  it("counts orderable provinces that have an order", () => {
    expect(countOrders([phaseState()], [order("lon"), order("edi")])).toEqual({
      submitted: 2,
      total: 3,
    });
  });

  it("ignores other nations' phase states", () => {
    const other = phaseState({
      member: { isCurrentUser: false } as PhaseState["member"],
      orderableProvinces: [province("par")],
    });
    expect(countOrders([other, phaseState()], [order("lon")])).toEqual({
      submitted: 1,
      total: 3,
    });
  });

  it("caps the total at maxOrders in an adjustment phase", () => {
    expect(countOrders([phaseState({ maxOrders: 1 })], [])).toEqual({
      submitted: 0,
      total: 1,
    });
  });

  it("returns null when the user is not a member", () => {
    expect(
      countOrders(
        [phaseState({ member: { isCurrentUser: false } as PhaseState["member"] })],
        []
      )
    ).toBeNull();
  });

  it("returns null when nothing is orderable", () => {
    expect(countOrders([phaseState({ orderableProvinces: [] })], [])).toBeNull();
  });
});
