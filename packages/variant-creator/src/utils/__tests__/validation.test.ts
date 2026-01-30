import { describe, it, expect } from "vitest";
import { validateVariantJson, VariantDefinitionSchema } from "../validation";
import type { VariantDefinition } from "@/types/variant";

const createValidVariant = (): VariantDefinition => ({
  name: "Test Variant",
  description: "A test variant",
  author: "Test Author",
  version: "1.0.0",
  soloVictorySCCount: 18,
  nations: [
    { id: "england", name: "England", color: "#FF0000" },
    { id: "france", name: "France", color: "#0000FF" },
  ],
  provinces: [
    {
      id: "lon",
      elementId: "path1",
      name: "London",
      type: "coastal",
      path: "M0,0 L10,0 L10,10 Z",
      homeNation: "england",
      supplyCenter: true,
      startingUnit: { type: "Fleet" },
      adjacencies: ["eng", "wal"],
      labels: [{ text: "London", position: { x: 5, y: 5 }, source: "svg" }],
      unitPosition: { x: 5, y: 5 },
      dislodgedUnitPosition: { x: 20, y: 20 },
      supplyCenterPosition: { x: -7, y: -7 },
    },
    {
      id: "par",
      elementId: "path2",
      name: "Paris",
      type: "land",
      path: "M20,20 L30,20 L30,30 Z",
      homeNation: "france",
      supplyCenter: true,
      startingUnit: { type: "Army" },
      adjacencies: ["bur", "pic"],
      labels: [{ text: "Paris", position: { x: 25, y: 25 }, source: "svg" }],
      unitPosition: { x: 25, y: 25 },
      dislodgedUnitPosition: { x: 40, y: 40 },
      supplyCenterPosition: { x: 13, y: 13 },
    },
  ],
  namedCoasts: [],
  decorativeElements: [],
  dimensions: { width: 100, height: 100 },
});

describe("validateVariantJson", () => {
  it("accepts valid variant JSON", () => {
    const variant = createValidVariant();
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(true);
    if (result.valid) {
      expect(result.variant.name).toBe("Test Variant");
      expect(result.variant.provinces).toHaveLength(2);
    }
  });

  it("rejects invalid JSON syntax", () => {
    const result = validateVariantJson("{ invalid json }");

    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.error.code).toBe("INVALID_JSON");
      expect(result.error.message).toBe("Invalid JSON format");
    }
  });

  it("rejects JSON with missing required fields", () => {
    const incomplete = { name: "Test", description: "desc" };
    const json = JSON.stringify(incomplete);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.error.code).toBe("INVALID_SCHEMA");
      expect(result.error.message).toBe("Invalid variant structure");
      expect(result.error.details).toBeDefined();
    }
  });

  it("rejects variant with zero provinces", () => {
    const variant = createValidVariant();
    variant.provinces = [];
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.error.code).toBe("EMPTY_PROVINCES");
      expect(result.error.message).toBe("Variant must contain at least one province");
    }
  });

  it("rejects province with invalid type", () => {
    const variant = createValidVariant();
    (variant.provinces[0] as { type: string }).type = "invalid";
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.error.code).toBe("INVALID_SCHEMA");
      expect(result.error.details).toContain("provinces.0.type");
    }
  });

  it("rejects province with invalid starting unit type", () => {
    const variant = createValidVariant();
    (variant.provinces[0].startingUnit as { type: string }).type = "Tank";
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.error.code).toBe("INVALID_SCHEMA");
    }
  });

  it("accepts variant with null starting unit", () => {
    const variant = createValidVariant();
    variant.provinces[0].startingUnit = null;
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(true);
  });

  it("accepts variant with null home nation", () => {
    const variant = createValidVariant();
    variant.provinces[0].homeNation = null;
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(true);
  });

  it("rejects dimensions with negative values", () => {
    const variant = createValidVariant();
    variant.dimensions.width = -100;
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.error.code).toBe("INVALID_SCHEMA");
      expect(result.error.details).toContain("dimensions.width");
    }
  });

  it("accepts variant with named coasts", () => {
    const variant = createValidVariant();
    variant.provinces[0].type = "namedCoasts";
    variant.namedCoasts = [
      {
        id: "lon/nc",
        name: "London (North Coast)",
        parentId: "lon",
        path: "M0,0 L5,0 L5,5 Z",
        adjacencies: ["nth"],
        unitPosition: { x: 2, y: 2 },
        dislodgedUnitPosition: { x: 17, y: 17 },
      },
    ];
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(true);
    if (result.valid) {
      expect(result.variant.namedCoasts).toHaveLength(1);
    }
  });

  it("accepts variant with decorative elements and styles", () => {
    const variant = createValidVariant();
    variant.decorativeElements = [
      {
        id: "deco1",
        type: "path",
        content: "M0,0 L100,100",
        styles: { fill: "#000", stroke: "#FFF" },
      },
    ];
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(true);
    if (result.valid) {
      expect(result.variant.decorativeElements).toHaveLength(1);
    }
  });

  it("accepts labels with optional fields", () => {
    const variant = createValidVariant();
    variant.provinces[0].labels = [
      {
        text: "London",
        position: { x: 5, y: 5 },
        source: "svg",
        rotation: 45,
        styles: {
          fontSize: "12px",
          fontFamily: "Arial",
          fontWeight: "bold",
          fill: "#000",
        },
      },
    ];
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(true);
    if (result.valid) {
      expect(result.variant.provinces[0].labels[0].rotation).toBe(45);
    }
  });

  it("accepts generated label source", () => {
    const variant = createValidVariant();
    variant.provinces[0].labels = [
      { text: "Gen", position: { x: 1, y: 1 }, source: "generated" },
    ];
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(true);
  });

  it("rejects invalid label source", () => {
    const variant = createValidVariant();
    (variant.provinces[0].labels[0] as { source: string }).source = "manual";
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.error.code).toBe("INVALID_SCHEMA");
    }
  });

  it("accepts empty nations array", () => {
    const variant = createValidVariant();
    variant.nations = [];
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(true);
  });

  it("rejects negative soloVictorySCCount", () => {
    const variant = createValidVariant();
    variant.soloVictorySCCount = -1;
    const json = JSON.stringify(variant);

    const result = validateVariantJson(json);

    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.error.code).toBe("INVALID_SCHEMA");
    }
  });
});

describe("VariantDefinitionSchema", () => {
  it("is exported for external use", () => {
    expect(VariantDefinitionSchema).toBeDefined();
    expect(VariantDefinitionSchema.safeParse).toBeInstanceOf(Function);
  });
});
