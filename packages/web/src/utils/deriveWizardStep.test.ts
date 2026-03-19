import { describe, it, expect } from "vitest";
import { deriveWizardStep, FieldValue, OrderOption } from "./deriveWizardStep";

const FIELD_ORDER: Record<string, string[]> = {
  Hold: ["source", "orderType"],
  Disband: ["source", "orderType"],
  Move: ["source", "orderType", "target", "namedCoast"],
  MoveViaConvoy: ["source", "orderType", "target"],
  Support: ["source", "orderType", "aux", "target"],
  Convoy: ["source", "orderType", "aux", "target"],
  Build: ["source", "orderType", "unitType", "namedCoast"],
};

const fv = (id: string, label?: string): FieldValue => ({
  id,
  label: label ?? id,
});

const option = (overrides: Partial<OrderOption>): OrderOption => ({
  source: null,
  orderType: null,
  target: null,
  aux: null,
  unitType: null,
  namedCoast: null,
  ...overrides,
});

describe("deriveWizardStep", () => {
  it("1. Fresh start (no selections) - two sources available", () => {
    const orders = [
      option({ source: fv("lon", "London"), orderType: fv("Hold", "Hold") }),
      option({ source: fv("edi", "Edinburgh"), orderType: fv("Hold", "Hold") }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {});
    expect(result.nextField).toBe("source");
    expect(result.choices).toEqual([fv("lon", "London"), fv("edi", "Edinburgh")]);
    expect(result.isComplete).toBe(false);
  });

  it("2. Source selected, multiple order types", () => {
    const orders = [
      option({ source: fv("lon"), orderType: fv("Hold") }),
      option({ source: fv("lon"), orderType: fv("Move"), target: fv("eng") }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, { source: "lon" });
    expect(result.nextField).toBe("orderType");
    expect(result.choices).toEqual([fv("Hold"), fv("Move")]);
  });

  it("3. Source selected, single order type → auto-advance", () => {
    const orders = [
      option({ source: fv("lon"), orderType: fv("Hold") }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, { source: "lon" });
    expect(result.isComplete).toBe(true);
    expect(result.selectedArray).toEqual(["lon", "Hold"]);
  });

  it("4. Hold complete", () => {
    const orders = [
      option({ source: fv("lon"), orderType: fv("Hold") }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {
      source: "lon",
      orderType: "Hold",
    });
    expect(result.isComplete).toBe(true);
    expect(result.selectedArray).toEqual(["lon", "Hold"]);
  });

  it("5. Move → select target", () => {
    const orders = [
      option({ source: fv("lon"), orderType: fv("Move"), target: fv("eng") }),
      option({ source: fv("lon"), orderType: fv("Move"), target: fv("nth") }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {
      source: "lon",
      orderType: "Move",
    });
    expect(result.nextField).toBe("target");
    expect(result.choices).toEqual([fv("eng"), fv("nth")]);
  });

  it("6. Move → target, no coast (namedCoast auto-skipped)", () => {
    const orders = [
      option({ source: fv("lon"), orderType: fv("Move"), target: fv("eng") }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {
      source: "lon",
      orderType: "Move",
      target: "eng",
    });
    expect(result.isComplete).toBe(true);
    expect(result.selectedArray).toEqual(["lon", "Move", "eng"]);
  });

  it("7. Move → target with named coast", () => {
    const orders = [
      option({
        source: fv("mid"),
        orderType: fv("Move"),
        target: fv("spa"),
        namedCoast: fv("spa/nc"),
      }),
      option({
        source: fv("mid"),
        orderType: fv("Move"),
        target: fv("spa"),
        namedCoast: fv("spa/sc"),
      }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {
      source: "mid",
      orderType: "Move",
      target: "spa",
    });
    expect(result.nextField).toBe("namedCoast");
    expect(result.choices).toEqual([fv("spa/nc"), fv("spa/sc")]);
  });

  it("8. Support → select aux", () => {
    const orders = [
      option({
        source: fv("lon"),
        orderType: fv("Support"),
        aux: fv("wal"),
        target: fv("yor"),
      }),
      option({
        source: fv("lon"),
        orderType: fv("Support"),
        aux: fv("edi"),
        target: fv("nth"),
      }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {
      source: "lon",
      orderType: "Support",
    });
    expect(result.nextField).toBe("aux");
    expect(result.choices).toEqual([fv("wal"), fv("edi")]);
  });

  it("9. Support → aux → target", () => {
    const orders = [
      option({
        source: fv("lon"),
        orderType: fv("Support"),
        aux: fv("wal"),
        target: fv("yor"),
      }),
      option({
        source: fv("lon"),
        orderType: fv("Support"),
        aux: fv("wal"),
        target: fv("eng"),
      }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {
      source: "lon",
      orderType: "Support",
      aux: "wal",
    });
    expect(result.nextField).toBe("target");
    expect(result.choices).toEqual([fv("yor"), fv("eng")]);
  });

  it("10. Build → unitType", () => {
    const orders = [
      option({
        source: fv("mun"),
        orderType: fv("Build"),
        unitType: fv("Army"),
      }),
      option({
        source: fv("mun"),
        orderType: fv("Build"),
        unitType: fv("Fleet"),
      }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {
      source: "mun",
      orderType: "Build",
    });
    expect(result.nextField).toBe("unitType");
    expect(result.choices).toEqual([fv("Army"), fv("Fleet")]);
  });

  it("11. Build Fleet → coast exists", () => {
    const orders = [
      option({
        source: fv("stp"),
        orderType: fv("Build"),
        unitType: fv("Fleet"),
        namedCoast: fv("stp/nc"),
      }),
      option({
        source: fv("stp"),
        orderType: fv("Build"),
        unitType: fv("Fleet"),
        namedCoast: fv("stp/sc"),
      }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {
      source: "stp",
      orderType: "Build",
      unitType: "Fleet",
    });
    expect(result.nextField).toBe("namedCoast");
    expect(result.choices).toEqual([fv("stp/nc"), fv("stp/sc")]);
  });

  it("12. Build Fleet → no coast", () => {
    const orders = [
      option({
        source: fv("bre"),
        orderType: fv("Build"),
        unitType: fv("Fleet"),
      }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {
      source: "bre",
      orderType: "Build",
      unitType: "Fleet",
    });
    expect(result.isComplete).toBe(true);
    expect(result.selectedArray).toEqual(["bre", "Build", "Fleet"]);
  });

  it("13. Empty orders array", () => {
    const result = deriveWizardStep([], FIELD_ORDER, {});
    expect(result.nextField).toBe(null);
    expect(result.choices).toEqual([]);
    expect(result.isComplete).toBe(false);
  });

  it("14. Single order → full auto-advance", () => {
    const orders = [
      option({ source: fv("lon"), orderType: fv("Hold") }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {});
    expect(result.isComplete).toBe(true);
    expect(result.selectedArray).toEqual(["lon", "Hold"]);
    expect(result.resolvedSelections["source"]).toBe("lon");
    expect(result.resolvedSelections["orderType"]).toBe("Hold");
  });

  it("15. selectedArray ordering for Move", () => {
    const orders = [
      option({
        source: fv("lon"),
        orderType: fv("Move"),
        target: fv("eng"),
      }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {
      source: "lon",
      orderType: "Move",
      target: "eng",
    });
    expect(result.isComplete).toBe(true);
    expect(result.selectedArray).toEqual(["lon", "Move", "eng"]);
  });

  it("16. selectedArray ordering for Support", () => {
    const orders = [
      option({
        source: fv("lon"),
        orderType: fv("Support"),
        aux: fv("wal"),
        target: fv("yor"),
      }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {
      source: "lon",
      orderType: "Support",
      aux: "wal",
      target: "yor",
    });
    expect(result.isComplete).toBe(true);
    expect(result.selectedArray).toEqual(["lon", "Support", "wal", "yor"]);
  });

  it("17. Convoy complete", () => {
    const orders = [
      option({
        source: fv("nth"),
        orderType: fv("Convoy"),
        aux: fv("yor"),
        target: fv("bel"),
      }),
    ];
    const result = deriveWizardStep(orders, FIELD_ORDER, {
      source: "nth",
      orderType: "Convoy",
      aux: "yor",
      target: "bel",
    });
    expect(result.isComplete).toBe(true);
    expect(result.selectedArray).toEqual(["nth", "Convoy", "yor", "bel"]);
  });
});
