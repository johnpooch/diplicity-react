import type {
  Nation,
  Order,
} from "../../api/generated/endpoints";
import type { OrderState, RenderState, UnitState } from "./mapRenderer";

type PhaseForRender = {
  units: Array<{
    province: { id: string };
    nation: { name: string };
    type: string;
    dislodged: boolean;
  }>;
  supplyCenters: Array<{
    province: { id: string };
    nation: { name: string };
  }>;
  provinceNations?: Record<string, string> | string;
};

const orderSourceId = (order: Order): string => {
  if (order.orderType === "Build") {
    return order.namedCoast?.id ?? order.source.id;
  }
  return order.sourceCoast?.id ?? order.source.id;
};

const orderTargetId = (order: Order): string | undefined => {
  if (order.orderType === "Move" || order.orderType === "MoveViaConvoy") {
    return order.namedCoast?.id ?? order.target?.id;
  }
  if (order.orderType === "Support") {
    return order.targetCoast?.id ?? order.target?.id ?? undefined;
  }
  return order.target?.id ?? undefined;
};

export const toRenderState = (
  variant: { nations: Nation[] },
  phase: PhaseForRender,
  orders: Order[],
  selected: string[],
  highlighted: string[] = [],
  civilDisorderNations: string[] = []
): RenderState => {
  const nationColors: Record<string, string> = {};
  for (const nation of variant.nations) {
    nationColors[nation.name] = nation.color;
  }

  const cdNations = new Set(civilDisorderNations);

  const units: UnitState[] = phase.units.map((unit) => ({
    province: unit.province.id,
    nation: unit.nation.name,
    type: unit.type as "Army" | "Fleet",
    dislodged: unit.dislodged,
    civilDisorder: cdNations.has(unit.nation.name),
  }));

  const supplyCenters = phase.supplyCenters.map((sc) => ({
    province: sc.province.id,
    nation: sc.nation.name,
  }));

  const nonScProvinceColors: Record<string, string> = {};
  const rawPN = phase.provinceNations;
  const pnMap: Record<string, string> =
    typeof rawPN === "string" ? (rawPN ? JSON.parse(rawPN) : {}) : (rawPN ?? {});
  for (const [provinceId, nationName] of Object.entries(pnMap)) {
    const color = nationColors[nationName];
    if (color) nonScProvinceColors[provinceId] = color;
  }

  const orderStates: OrderState[] = orders.map((order) => {
    const target = orderTargetId(order);
    const aux = order.aux?.id || undefined;
    return {
      type: order.orderType,
      nation: order.nation.name,
      source: orderSourceId(order),
      ...(target ? { target } : {}),
      ...(aux ? { aux } : {}),
      ...(order.unitType
        ? { unitType: order.unitType as "Army" | "Fleet" }
        : {}),
      failed: Boolean(
        order.resolution && order.resolution.status !== "Succeeded"
      ),
    };
  });

  return {
    nationColors,
    supplyCenters,
    nonScProvinceColors,
    units,
    orders: orderStates,
    selected,
    highlighted,
  };
};
