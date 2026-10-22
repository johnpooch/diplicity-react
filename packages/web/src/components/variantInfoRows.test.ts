import { describe, it, expect } from "vitest";

import type { Variant, VariantNation } from "@/api/generated/endpoints";
import { classicalVariant } from "@/mocks/fixtures/classical";
import { buildVariantInfoRows } from "./variantInfoRows";

const withTargets = (
  defaultTarget: number | null,
  targets: Record<string, number | null>
): Variant => ({
  ...classicalVariant,
  victoryConditions: {
    ...classicalVariant.victoryConditions,
    soloVictorySupplyCenters: defaultTarget,
  },
  nations: classicalVariant.nations.map(
    (nation): VariantNation => ({
      ...nation,
      soloVictorySupplyCenters:
        nation.nationId in targets ? targets[nation.nationId] : defaultTarget,
    })
  ),
});

const victoryRow = (variant: Variant) =>
  buildVariantInfoRows(variant).find(row => row.key === "victory");

describe("buildVariantInfoRows", () => {
  it("states the default target when every nation uses it", () => {
    expect(victoryRow(withTargets(18, {}))).toMatchObject({
      label: "Solo victory",
      value: "18 supply centres",
    });
    expect(victoryRow(withTargets(18, {}))?.text).toBeUndefined();
  });

  it("lists overridden nations and says every other nation uses the default", () => {
    expect(
      victoryRow(withTargets(18, { england: 15, russia: 20 }))
    ).toMatchObject({
      value: "18 supply centres",
      text: "England: 15 supply centres\nRussia: 20 supply centres\nEvery other nation: 18 supply centres",
    });
  });

  it("says other nations cannot win solo when there is no default", () => {
    expect(victoryRow(withTargets(null, { england: 1 }))).toMatchObject({
      value: "Varies by nation",
      text: "England: 1 supply centre\nOther nations cannot win solo",
    });
  });

  it("omits the victory row when no nation has a target", () => {
    expect(victoryRow(withTargets(null, {}))).toBeUndefined();
  });

  it("places the victory row before the start year", () => {
    expect(
      buildVariantInfoRows(withTargets(18, {})).map(row => row.key)
    ).toEqual(["description", "rules", "victory", "start-year", "author"]);
  });
});
