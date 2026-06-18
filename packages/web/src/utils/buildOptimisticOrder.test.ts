import { describe, it, expect } from "vitest";
import { buildOptimisticOrder } from "./buildOptimisticOrder";
import type { Province, Nation, Variant, PhaseRetrieve } from "../api/generated/endpoints";

const makeProvince = (id: string): Province => ({
  id,
  name: id,
  type: "land",
  supplyCenter: false,
  parentId: null,
  namedCoastIds: [],
});

const england: Nation = { nationId: "england", name: "England", color: "rgb(255,0,0)", flagUrl: null };
const france: Nation = { nationId: "france", name: "France", color: "rgb(0,0,255)", flagUrl: null };

const lon = makeProvince("lon");
const nth = makeProvince("nth");
const bre = makeProvince("bre");
const par = makeProvince("par");

const variant: Pick<Variant, "provinces"> = {
  provinces: [lon, nth, bre, par],
};

const phaseWithUnit = (provinceId: string, nation: Nation): Pick<PhaseRetrieve, "units" | "supplyCenters"> => ({
  units: [
    {
      type: "Army",
      nation,
      province: makeProvince(provinceId),
      dislodged: false,
      dislodgedBy: null,
    },
  ],
  supplyCenters: [],
});

const phaseWithSupplyCenter = (provinceId: string, nation: Nation): Pick<PhaseRetrieve, "units" | "supplyCenters"> => ({
  units: [],
  supplyCenters: [{ province: makeProvince(provinceId), nation }],
});

describe("buildOptimisticOrder", () => {
  it("builds a Move order with correct source, target, and nation", () => {
    const result = buildOptimisticOrder(
      { source: "lon", orderType: "Move", target: "nth" },
      variant,
      phaseWithUnit("lon", england)
    );

    expect(result).not.toBeNull();
    expect(result!.source.id).toBe("lon");
    expect(result!.target!.id).toBe("nth");
    expect(result!.orderType).toBe("Move");
    expect(result!.nation).toEqual(england);
  });

  it("builds a Hold order with target falling back to source", () => {
    const result = buildOptimisticOrder(
      { source: "par", orderType: "Hold" },
      variant,
      phaseWithUnit("par", france)
    );

    expect(result).not.toBeNull();
    expect(result!.source.id).toBe("par");
    expect(result!.target!.id).toBe("par");
    expect(result!.orderType).toBe("Hold");
  });

  it("builds a Support order with correct aux and target", () => {
    const result = buildOptimisticOrder(
      { source: "lon", orderType: "Support", aux: "bre", target: "par" },
      variant,
      phaseWithUnit("lon", england)
    );

    expect(result).not.toBeNull();
    expect(result!.aux!.id).toBe("bre");
    expect(result!.target!.id).toBe("par");
  });

  it("resolves nation from phase.supplyCenters for Build orders", () => {
    const result = buildOptimisticOrder(
      { source: "lon", orderType: "Build", unitType: "Army" },
      variant,
      phaseWithSupplyCenter("lon", england)
    );

    expect(result).not.toBeNull();
    expect(result!.nation).toEqual(england);
    expect(result!.unitType).toBe("Army");
  });

  it("sets resolution to Succeeded to prevent failure cross rendering", () => {
    const result = buildOptimisticOrder(
      { source: "lon", orderType: "Move", target: "nth" },
      variant,
      phaseWithUnit("lon", england)
    );

    expect(result!.resolution.status).toBe("Succeeded");
    expect(result!.resolution.by).toBeNull();
  });

  it("returns null when source province is not in variant.provinces", () => {
    const result = buildOptimisticOrder(
      { source: "unknown", orderType: "Hold" },
      variant,
      phaseWithUnit("lon", england)
    );

    expect(result).toBeNull();
  });

  it("returns null when no unit or supply center found at source", () => {
    const result = buildOptimisticOrder(
      { source: "lon", orderType: "Move", target: "nth" },
      variant,
      { units: [], supplyCenters: [] }
    );

    expect(result).toBeNull();
  });

  it("returns null when resolvedSelections is missing source", () => {
    const result = buildOptimisticOrder(
      { orderType: "Hold" },
      variant,
      phaseWithUnit("lon", england)
    );

    expect(result).toBeNull();
  });

  it("returns null when resolvedSelections is missing orderType", () => {
    const result = buildOptimisticOrder(
      { source: "lon" },
      variant,
      phaseWithUnit("lon", england)
    );

    expect(result).toBeNull();
  });

  it("aux falls back to source when not in selections", () => {
    const result = buildOptimisticOrder(
      { source: "lon", orderType: "Support", target: "par" },
      variant,
      phaseWithUnit("lon", england)
    );

    expect(result).not.toBeNull();
    expect(result!.aux!.id).toBe("lon");
  });

  it("defaults unitType to Army when not in selections", () => {
    const result = buildOptimisticOrder(
      { source: "lon", orderType: "Move", target: "nth" },
      variant,
      phaseWithUnit("lon", england)
    );

    expect(result!.unitType).toBe("Army");
  });

  it("namedCoast falls back to target (not source) when not in selections", () => {
    const result = buildOptimisticOrder(
      { source: "lon", orderType: "Move", target: "nth" },
      variant,
      phaseWithUnit("lon", england)
    );

    expect(result!.namedCoast!.id).toBe("nth");
  });
});
