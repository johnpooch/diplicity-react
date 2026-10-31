import { describe, it, expect } from "vitest";

import type { Variant, VariantNation } from "@/api/generated/endpoints";
import { buildVariantInfoRows } from "./variantInfoRows";

const variantRules = "Orders are written simultaneously.";

const nationNames = ["england", "russia", "turkey"];

const baseVariant: Variant = {
  id: "classical",
  name: "Classical",
  description: "",
  rules: variantRules,
  unitScaling: 1,
  status: "active",
  official: true,
  ownerId: null,
  ownerUsername: null,
  canEdit: false,
  victoryConditions: {
    soloVictorySupplyCenters: null,
    gameEndsYear: null,
    drawAfterYear: null,
  },
  svgUrl: null,
  nations: nationNames.map(
    (nationId): VariantNation => ({
      nationId,
      name: nationId.charAt(0).toUpperCase() + nationId.slice(1),
      color: "#000000",
      nonPlayable: false,
      flagUrl: null,
      soloVictorySupplyCenters: null,
    })
  ),
  provinces: [],
  templatePhase: { year: 1901, units: [], supplyCenters: [] },
};

const withTargets = (
  defaultTarget: number | null,
  targets: Record<string, number | null>
): Variant => ({
  ...baseVariant,
  victoryConditions: {
    ...baseVariant.victoryConditions,
    soloVictorySupplyCenters: defaultTarget,
  },
  nations: baseVariant.nations.map(
    (nation): VariantNation => ({
      ...nation,
      soloVictorySupplyCenters:
        nation.nationId in targets ? targets[nation.nationId] : defaultTarget,
    })
  ),
});

const rulesText = (variant: Variant) =>
  buildVariantInfoRows(variant).find(row => row.key === "rules")?.text;

describe("buildVariantInfoRows", () => {
  it("opens the rules with the default target when every nation uses it", () => {
    expect(rulesText(withTargets(18, {}))).toBe(
      `Solo victory: 18 supply centres.\n\n${variantRules}`
    );
  });

  it("names the nations with their own target", () => {
    expect(
      rulesText(withTargets(18, { england: 15, russia: 20, turkey: 16 }))
    ).toBe(
      `Solo victory: 18 supply centres, except England (15), Russia (20) and Turkey (16).\n\n${variantRules}`
    );
  });

  it("says other nations cannot win solo when there is no default", () => {
    expect(rulesText(withTargets(null, { england: 15 }))).toBe(
      `Solo victory: England (15) supply centres. Other nations cannot win solo.\n\n${variantRules}`
    );
  });

  it("shows the variant's rules alone when no nation has a target", () => {
    expect(rulesText(withTargets(null, {}))).toBe(variantRules);
  });

  it("shows the victory rule when the variant has no rules of its own", () => {
    expect(rulesText({ ...withTargets(18, {}), rules: "" })).toBe(
      "Solo victory: 18 supply centres."
    );
  });

  it("omits the rules row when there is neither a target nor rules", () => {
    expect(rulesText({ ...withTargets(null, {}), rules: "" })).toBeUndefined();
  });
});
