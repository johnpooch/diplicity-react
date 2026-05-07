import type {
  Order,
  Province,
  Variant,
  PhaseRetrieve,
} from "../api/generated/endpoints";

function buildOptimisticOrder(
  resolvedSelections: Record<string, string>,
  variant: Pick<Variant, "provinces">,
  phase: Pick<PhaseRetrieve, "units" | "supplyCenters">
): Order | null {
  const sourceId = resolvedSelections["source"];
  const orderType = resolvedSelections["orderType"];
  if (!sourceId || !orderType) return null;

  const findProvince = (id: string | undefined): Province | null =>
    id ? (variant.provinces.find((p) => p.id === id) ?? null) : null;

  const source = findProvince(sourceId);
  if (!source) return null;

  const unit = phase.units.find((u) => u.province.id === sourceId);
  const nation =
    unit?.nation ??
    phase.supplyCenters.find((sc) => sc.province.id === sourceId)?.nation;
  if (!nation) return null;

  const target = findProvince(resolvedSelections["target"]) ?? source;
  const aux = findProvince(resolvedSelections["aux"]) ?? source;
  const namedCoast = findProvince(resolvedSelections["namedCoast"]) ?? target;

  return {
    source,
    sourceCoast: null,
    target,
    aux,
    namedCoast,
    // "Succeeded" prevents the failure cross from rendering on the pending order
    resolution: { status: "Succeeded", by: null },
    options: [],
    orderType: orderType as Order["orderType"],
    unitType: (resolvedSelections["unitType"] as Order["unitType"]) ?? "Army",
    nation,
    complete: null,
    step: null,
    title: null,
    summary: null,
  };
}

export { buildOptimisticOrder };
