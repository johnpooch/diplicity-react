import type { Variant } from "@/api/generated/endpoints";
import { classicalVariant } from "./classical";
import cantonGodip from "./data/canton-godip.json";
import hundredGodip from "./data/hundred-godip.json";
import vietnamGodip from "./data/vietnam-war-godip.json";
import youngstownGodip from "./data/youngstown-redux-godip.json";

interface GodipVariant {
  id: string;
  name: string;
  description?: string;
  author?: string;
  nations: { name: string; color: string }[];
  provinces: { id: string; name: string }[];
  initial_phase: { season: string; year: number; type: string };
  initial_units: { type: string; nation: string; province: string }[];
  initial_supply_centers: { nation: string; province: string }[];
}

const buildVariant = (raw: GodipVariant): Variant =>
  ({
    id: raw.id,
    name: raw.name,
    description: raw.description ?? "",
    author: raw.author ?? "",
    rules: "",
    status: "published",
    official: true,
    ownerId: null,
    ownerUsername: null,
    canEdit: false,
    victoryConditions: {
      soloVictorySupplyCenters: 18,
      gameEndsYear: null,
      drawAfterYear: null,
    },
    svgUrl: `/mock-assets/${raw.id}.d.svg`,
    nations: raw.nations.map(n => ({
      nationId: n.name.toLowerCase().replace(/\s+/g, "-"),
      name: n.name,
      color: n.color,
      flagUrl: null,
    })),
    provinces: raw.provinces.map(p => ({
      id: p.id,
      name: p.name,
      parentId: null,
    })),
    templatePhase: {
      year: raw.initial_phase.year,
      units: raw.initial_units.map(u => ({
        type: u.type,
        dislodged: false,
        nation: { name: u.nation },
        province: { id: u.province },
      })),
      supplyCenters: raw.initial_supply_centers.map(sc => ({
        nation: { name: sc.nation },
        province: { id: sc.province },
      })),
    },
  }) as unknown as Variant;

export const extraVariants: Variant[] = [
  buildVariant(cantonGodip as GodipVariant),
  buildVariant(hundredGodip as GodipVariant),
  buildVariant(vietnamGodip as GodipVariant),
  buildVariant(youngstownGodip as GodipVariant),
];

export const allVariants: Variant[] = [classicalVariant, ...extraVariants];

export const draftVariant: Variant = {
  ...classicalVariant,
  id: "my-draft",
  name: "My Draft Variant",
  status: "draft",
  official: false,
  ownerId: 1,
  ownerUsername: "testuser",
  canEdit: true,
};
