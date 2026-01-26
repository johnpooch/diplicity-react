import { Province } from "../api/generated/endpoints";

/**
 * Check if a province has named coasts
 */
export function hasNamedCoasts(province: Province): boolean {
  return province.namedCoastIds.length > 0;
}

/**
 * Check if a province is a named coast
 */
export function isNamedCoast(province: Province): boolean {
  return province.parentId !== null;
}

/**
 * Get the main province for a given province (returns self if already main province)
 */
export function getMainProvince(provinces: Province[], provinceId: string): Province | undefined {
  const province = provinces.find(p => p.id === provinceId);
  if (!province) return undefined;

  if (isNamedCoast(province)) {
    return provinces.find(p => p.id === province.parentId);
  }

  return province;
}

/**
 * Get all provinces in the same group (main province + its named coasts)
 */
export function getProvinceGroup(provinces: Province[], provinceId: string): Province[] {
  const province = provinces.find(p => p.id === provinceId);
  if (!province) return [];

  if (isNamedCoast(province)) {
    // For named coast, return parent + all siblings
    const parent = provinces.find(p => p.id === province.parentId);
    if (parent) {
      const namedCoasts = provinces.filter(p => parent.namedCoastIds.includes(p.id));
      return [parent, ...namedCoasts];
    }
  } else if (hasNamedCoasts(province)) {
    // For main province, return self + named coasts
    const namedCoasts = provinces.filter(p => province.namedCoastIds.includes(p.id));
    return [province, ...namedCoasts];
  }

  return [province];
}

/**
 * Determine which provinces should be rendered based on highlighted options
 *
 * Core logic:
 * - Default: Show main provinces only
 * - When named coasts are highlighted: Hide main province, show only highlighted named coasts
 * - When main provinces are highlighted: Show main provinces only
 */
export function determineRenderableProvinces(
  allProvinces: Province[],
  highlightedProvinceIds: string[]
): string[] {
  const renderableProvinces = new Set<string>();

  // Group all provinces by their main province ID
  const provinceGroups = new Map<string, Province[]>();

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