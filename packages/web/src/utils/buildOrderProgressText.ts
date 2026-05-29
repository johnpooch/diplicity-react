import type { PhaseRetrieve } from "../api/generated/endpoints";

function unitAbbrev(type: string | undefined): string {
  if (type === "Army") return "A";
  if (type === "Fleet") return "F";
  return "";
}

function buildOrderProgressText(
  resolvedSelections: Record<string, string>,
  resolvedLabels: Record<string, string>,
  phase: PhaseRetrieve
): string {
  const { source, orderType, target, aux, unitType } = resolvedSelections;

  if (!source) return "";

  const unitsByProvince = Object.fromEntries(
    phase.units.map((u) => [u.province.id, u])
  );

  const sourceName = resolvedLabels["source"] ?? source;

  if (!orderType) {
    const unit = unitsByProvince[source];
    return unit ? `${unitAbbrev(unit.type)} ${sourceName}` : sourceName;
  }

  if (orderType === "Build") {
    if (!unitType) return `Build in ${sourceName} ...`;
    return `Build ${unitType} in ${sourceName}`;
  }

  const unit = unitsByProvince[source];
  const sourceLabel = unit ? `${unitAbbrev(unit.type)} ${sourceName}` : sourceName;

  if (orderType === "Hold") return `${sourceLabel} Hold`;
  if (orderType === "Disband") return `${sourceLabel} Disband`;

  if (orderType === "Move" || orderType === "MoveViaConvoy") {
    const via = orderType === "MoveViaConvoy" ? " via Convoy" : "";
    if (!target) return `${sourceLabel} Move${via} to ...`;
    return `${sourceLabel} Move${via} to ${resolvedLabels["target"] ?? target}`;
  }

  if (orderType === "Support") {
    if (!aux) return `${sourceLabel} Supports ...`;
    const auxUnit = unitsByProvince[aux];
    const auxName = resolvedLabels["aux"] ?? aux;
    const auxLabel = auxUnit ? `${unitAbbrev(auxUnit.type)} ${auxName}` : auxName;
    if (!target) return `${sourceLabel} Supports ${auxLabel} ...`;
    return `${sourceLabel} Supports ${auxLabel} to ${resolvedLabels["target"] ?? target}`;
  }

  if (orderType === "Convoy") {
    if (!aux) return `${sourceLabel} Convoys ...`;
    const auxUnit = unitsByProvince[aux];
    const auxName = resolvedLabels["aux"] ?? aux;
    const auxLabel = auxUnit ? `${unitAbbrev(auxUnit.type)} ${auxName}` : auxName;
    if (!target) return `${sourceLabel} Convoys ${auxLabel} to ...`;
    return `${sourceLabel} Convoys ${auxLabel} to ${resolvedLabels["target"] ?? target}`;
  }

  return sourceLabel;
}

export { buildOrderProgressText, unitAbbrev };
