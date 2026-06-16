import { Province } from "../api/generated/endpoints";

/**
 * Determine which provinces should be rendered based on highlighted options
 *
 * Core logic:
 * - Default: Show main provinces only
 * - When named coasts are highlighted: Hide main province, show only highlighted named coasts
 * - When main provinces are highlighted: Show main provinces only
 */
type ProvinceWithParent = Pick<Province, "id" | "parentId">;

export function determineRenderableProvinces(
  allProvinces: ProvinceWithParent[],
  highlightedProvinceIds: string[]
): string[] {
  const renderableProvinces = new Set<string>();

  // Group all provinces by their main province ID
  const provinceGroups = new Map<string, ProvinceWithParent[]>();

  for (const province of allProvinces) {
    const mainProvinceId = province.parentId || province.id;
    if (!provinceGroups.has(mainProvinceId)) {
      provinceGroups.set(mainProvinceId, []);
    }
    provinceGroups.get(mainProvinceId)!.push(province);
  }

  // For each group, determine which provinces should be rendered
  for (const [mainProvinceId, group] of provinceGroups) {
    const mainProvince = group.find(p => p.id === mainProvinceId);

    // Check which provinces in this group are highlighted
    const highlightedInGroup = group.filter(p => highlightedProvinceIds.includes(p.id));

    if (highlightedInGroup.length === 0) {
      // Nothing highlighted in this group - show main province only
      if (mainProvince) {
        renderableProvinces.add(mainProvince.id);
      }
    } else {
      // Something is highlighted - show only the highlighted provinces
      highlightedInGroup.forEach(p => renderableProvinces.add(p.id));
    }
  }

  return Array.from(renderableProvinces);
}