import type {
  Order,
  Province,
  Variant,
  VariantProvince,
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

  // VariantProvince only carries { id, parentId } but the Order shape demands
  // a full Province. Downstream consumers of an optimistic order (the map
  // renderer, order de-duping in GameMap) only read .id, so the cast is safe
  // for this in-flight pending order — it is replaced by the server response.
  const findProvince = (id: string | undefined): Province | null => {
    if (!id) return null;
    const slim: VariantProvince | undefined = variant.provinces.find(
      (p) => p.id === id
    );
    return slim ? (slim as unknown as Province) : null;
  };

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
    targetCoast: null,
    target,
    aux,
    namedCoast,
    // "Succeeded" prevents the failure cross from rendering on the pending order
    resolution: { status: "Succeeded", by: null },
    orderType: orderType as Order["orderType"],
    unitType: (resolvedSelections["unitType"] as Order["unitType"]) ?? "Army",
    nation,
    isImplicit: false,
    complete: null,
    step: null,
    title: null,
    summary: null,
  };
}

export { buildOptimisticOrder };
