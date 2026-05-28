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
};

type VariantProvinceForRender = {
  id: string;
  parentId: string | null;
  type: string;
  supplyCenter: boolean;
  adjacencies: readonly string[];
};

type DominanceRuleForRender = {
  province: string;
  nation: string;
  dependencies: ReadonlyArray<{ province: string; nation: string }>;
};

const computeNonScProvinceColors = (
  provinces: VariantProvinceForRender[],
  supplyCenters: Array<{ province: string; nation: string }>,
  nationColors: Record<string, string>,
  nationIdToName: Map<string, string>,
  dominanceRules: DominanceRuleForRender[]
): Record<string, string> => {
  const provinceById = new Map(provinces.map((p) => [p.id, p]));
  const scOwnerMap = new Map(supplyCenters.map((sc) => [sc.province, sc.nation]));

  const resolveToScId = (id: string): string | null => {
    const p = provinceById.get(id);
    if (!p) return null;
    if (p.supplyCenter) return id;
    if (p.parentId && provinceById.get(p.parentId)?.supplyCenter) return p.parentId;
    return null;
  };

  const rulesByProvince = new Map<string, DominanceRuleForRender[]>();
  for (const rule of dominanceRules) {
    const list = rulesByProvince.get(rule.province) ?? [];
    list.push(rule);
    rulesByProvince.set(rule.province, list);
  }

  const UNOWNED_MARKERS = new Set(["Empty", "Neutral"]);

  const dependencyMatches = (dep: { province: string; nation: string }): boolean => {
    if (UNOWNED_MARKERS.has(dep.nation)) {
      return !scOwnerMap.has(dep.province);
    }
    const nationName = nationIdToName.get(dep.nation);
    if (!nationName) return false;
    return scOwnerMap.get(dep.province) === nationName;
  };

  const defaultColor = (province: VariantProvinceForRender): string | null => {
    const adjacentScIds = new Set<string>();
    for (const adjId of (province.adjacencies ?? [])) {
      const scId = resolveToScId(adjId);
      if (scId) adjacentScIds.add(scId);
    }
    if (adjacentScIds.size === 0) return null;

    let owner: string | null = null;
    for (const scId of adjacentScIds) {
      const scOwner = scOwnerMap.get(scId);
      if (!scOwner) return null;
      if (owner === null) {
        owner = scOwner;
      } else if (owner !== scOwner) {
        return null;
      }
    }
    return owner && nationColors[owner] ? nationColors[owner] : null;
  };

  const colors: Record<string, string> = {};
  for (const province of provinces) {
    if (province.supplyCenter) continue;
    if (province.type === "sea" || province.type === "named_coast") continue;

    const rules = rulesByProvince.get(province.id);
    if (rules) {
      const matchedRule = rules.find((r) => r.dependencies.every(dependencyMatches));
      if (matchedRule) {
        const nationName = nationIdToName.get(matchedRule.nation);
        if (nationName && nationColors[nationName]) {
          colors[province.id] = nationColors[nationName];
        }
        continue;
      }
    }

    const color = defaultColor(province);
    if (color) {
      colors[province.id] = color;
    }
  }

  return colors;
};

const orderSourceId = (order: Order): string => {
  if (order.orderType === "Build") {
    return order.namedCoast?.id ?? order.source.id;
  }
  if (order.orderType === "Support" || order.orderType === "Convoy") {
    return order.source.id;
  }
  return order.sourceCoast?.id ?? order.source.id;
};

const orderTargetId = (order: Order): string | undefined => {
  if (order.orderType === "Move" || order.orderType === "MoveViaConvoy") {
    return order.namedCoast?.id ?? order.target?.id;
  }
  return order.target?.id ?? undefined;
};

export const toRenderState = (
  variant: {
    nations: Nation[];
    provinces?: VariantProvinceForRender[];
    dominanceRules?: DominanceRuleForRender[];
  },
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

  const nationIdToName = new Map(variant.nations.map((n) => [n.nationId, n.name]));

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

  const nonScProvinceColors =
    variant.provinces && variant.provinces.length > 0
      ? computeNonScProvinceColors(
          variant.provinces,
          supplyCenters,
          nationColors,
          nationIdToName,
          variant.dominanceRules ?? []
        )
      : {};

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
