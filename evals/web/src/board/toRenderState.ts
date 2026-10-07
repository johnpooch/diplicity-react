import type { BoardState, OrderDetail } from "../api";
import type { OrderState, OrderType, RenderState } from "./mapRenderer";
import { NATION_COLORS } from "./nationColors";

const parentProvince = (province: string): string => province.split("/")[0];

const orderSource = (order: OrderDetail, unitProvinces: Map<string, string>): string => {
  if (order.order_type === "Build") {
    return order.named_coast ?? order.source;
  }
  return unitProvinces.get(order.source) ?? order.source;
};

const orderTarget = (order: OrderDetail): string | null => {
  if (order.order_type === "Hold") {
    return null;
  }
  if (order.order_type === "Move" || order.order_type === "MoveViaConvoy") {
    return order.named_coast ?? order.target;
  }
  return order.target;
};

export const toRenderState = (
  board: BoardState,
  orders: OrderDetail[]
): RenderState => {
  const unitProvinces = new Map(
    [...board.units]
      .sort((a, b) => Number(a.dislodged) - Number(b.dislodged))
      .map(unit => [parentProvince(unit.province), unit.province])
  );

  const orderStates: OrderState[] = orders.map(order => {
    const target = orderTarget(order);
    return {
      type: order.order_type as OrderType,
      nation: board.nation,
      source: orderSource(order, unitProvinces),
      ...(target ? { target } : {}),
      ...(order.aux ? { aux: order.aux } : {}),
      ...(order.unit_type ? { unitType: order.unit_type as "Army" | "Fleet" } : {}),
    };
  });

  return {
    nationColors: NATION_COLORS,
    supplyCenters: board.supply_centers,
    units: board.units,
    orders: orderStates,
  };
};
