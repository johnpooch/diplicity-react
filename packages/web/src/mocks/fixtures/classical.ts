import type {
  Nation,
  Province,
  SupplyCenter,
  Unit,
  Variant,
} from "@/api/generated/endpoints";
import classicalVariantData from "./data/classical-variant.json";
import classicalProvincesData from "./data/classical-provinces.json";
import classicalStartData from "./data/classical-start.json";

export const classicalVariant = classicalVariantData as Variant;

export const classicalProvinces = classicalProvincesData as Province[];

export const province = (id: string): Province => {
  const found = classicalProvinces.find(p => p.id === id);
  if (!found) throw new Error(`Unknown classical province: ${id}`);
  return found;
};

export const nation = (nationId: string): Nation => {
  const found = classicalVariant.nations.find(n => n.nationId === nationId);
  if (!found) throw new Error(`Unknown classical nation: ${nationId}`);
  return found;
};

const nationByName = (name: string): Nation => {
  const found = classicalVariant.nations.find(n => n.name === name);
  if (!found) throw new Error(`Unknown classical nation name: ${name}`);
  return found;
};

export const classicalStartUnits: Unit[] = classicalStartData.units.map(u => ({
  type: u.type,
  nation: nationByName(u.nation),
  province: province(u.province),
  dislodged: false,
  dislodgedBy: null,
}));

export const classicalStartSupplyCenters: SupplyCenter[] =
  classicalStartData.supplyCenters.map(sc => ({
    nation: nationByName(sc.nation),
    province: province(sc.province),
  }));
