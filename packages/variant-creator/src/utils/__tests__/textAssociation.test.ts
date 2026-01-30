import { describe, it, expect, vi } from "vitest";
import {
  autoAssociateText,
  textElementToLabel,
  syncAssociationsToProvinces,
  buildAssociationsFromProvinces,
} from "../textAssociation";
import type { TextElement, Province, Label } from "@/types/variant";

vi.mock("../geometry", () => ({
  calculateCentroid: vi.fn((pathD: string) => {
    const match = pathD.match(/M(\d+),(\d+)/);
    if (match) {
      const x = parseInt(match[1], 10) + 10;
      const y = parseInt(match[2], 10) + 10;
      return { x, y };
    }
    return { x: 0, y: 0 };
  }),
}));

const createProvince = (
  id: string,
  centroidX: number,
  centroidY: number,
  labels: Label[] = []
): Province => ({
  id,
  elementId: `path_${id}`,
  name: id.charAt(0).toUpperCase() + id.slice(1),
  type: "land",
  path: `M${centroidX - 10},${centroidY - 10} L${centroidX + 10},${centroidY - 10} L${centroidX + 10},${centroidY + 10} L${centroidX - 10},${centroidY + 10} Z`,
  homeNation: null,
  supplyCenter: false,
  startingUnit: null,
  adjacencies: [],
  labels,
  unitPosition: { x: centroidX, y: centroidY },
  dislodgedUnitPosition: { x: centroidX + 15, y: centroidY + 15 },
  supplyCenterPosition: { x: centroidX - 12, y: centroidY - 12 },
});

const createTextElement = (
  content: string,
  x: number,
  y: number
): TextElement => ({
  content,
  x,
  y,
});

describe("autoAssociateText", () => {
  it("associates text with closest province within threshold", () => {
    const textElements: TextElement[] = [createTextElement("Berlin", 100, 100)];
    const provinces: Province[] = [
      createProvince("ber", 100, 100),
      createProvince("mun", 200, 200),
    ];

    const result = autoAssociateText(textElements, provinces);

    expect(result.get(0)).toBe("ber");
  });

  it("returns null for text outside threshold", () => {
    const textElements: TextElement[] = [createTextElement("Far Away", 500, 500)];
    const provinces: Province[] = [createProvince("ber", 100, 100)];

    const result = autoAssociateText(textElements, provinces);

    expect(result.get(0)).toBeNull();
  });

  it("handles multiple texts associating with same province", () => {
    const textElements: TextElement[] = [
      createTextElement("Berlin", 100, 95),
      createTextElement("BER", 100, 105),
    ];
    const provinces: Province[] = [createProvince("ber", 100, 100)];

    const result = autoAssociateText(textElements, provinces);

    expect(result.get(0)).toBe("ber");
    expect(result.get(1)).toBe("ber");
  });

  it("handles empty text elements array", () => {
    const textElements: TextElement[] = [];
    const provinces: Province[] = [createProvince("ber", 100, 100)];

    const result = autoAssociateText(textElements, provinces);

    expect(result.size).toBe(0);
  });

  it("handles empty provinces array", () => {
    const textElements: TextElement[] = [createTextElement("Berlin", 100, 100)];
    const provinces: Province[] = [];

    const result = autoAssociateText(textElements, provinces);

    expect(result.get(0)).toBeNull();
  });

  it("associates each text with closest province when multiple provinces exist", () => {
    const textElements: TextElement[] = [
      createTextElement("Berlin", 100, 100),
      createTextElement("Munich", 200, 200),
    ];
    const provinces: Province[] = [
      createProvince("ber", 100, 100),
      createProvince("mun", 200, 200),
    ];

    const result = autoAssociateText(textElements, provinces);

    expect(result.get(0)).toBe("ber");
    expect(result.get(1)).toBe("mun");
  });

  it("picks closest province when text is between two provinces", () => {
    const textElements: TextElement[] = [createTextElement("Text", 140, 100)];
    const provinces: Province[] = [
      createProvince("ber", 100, 100),
      createProvince("mun", 200, 100),
    ];

    const result = autoAssociateText(textElements, provinces);

    expect(result.get(0)).toBe("ber");
  });
});

describe("textElementToLabel", () => {
  it("converts text element to label with svg source", () => {
    const text: TextElement = {
      content: "Berlin",
      x: 100,
      y: 200,
      rotation: 45,
      styles: { fontSize: "12px", fill: "#000" },
    };

    const label = textElementToLabel(text);

    expect(label).toEqual({
      text: "Berlin",
      position: { x: 100, y: 200 },
      rotation: 45,
      source: "svg",
      styles: { fontSize: "12px", fill: "#000" },
    });
  });

  it("handles text element without optional fields", () => {
    const text: TextElement = {
      content: "Simple",
      x: 50,
      y: 75,
    };

    const label = textElementToLabel(text);

    expect(label).toEqual({
      text: "Simple",
      position: { x: 50, y: 75 },
      rotation: undefined,
      source: "svg",
      styles: undefined,
    });
  });
});

describe("syncAssociationsToProvinces", () => {
  it("adds labels to provinces based on associations", () => {
    const textElements: TextElement[] = [
      createTextElement("Berlin", 100, 100),
      createTextElement("Munich", 200, 200),
    ];
    const provinces: Province[] = [
      createProvince("ber", 100, 100),
      createProvince("mun", 200, 200),
    ];
    const associations = new Map<number, string | null>([
      [0, "ber"],
      [1, "mun"],
    ]);

    const result = syncAssociationsToProvinces(
      textElements,
      provinces,
      associations
    );

    expect(result[0].labels).toHaveLength(1);
    expect(result[0].labels[0].text).toBe("Berlin");
    expect(result[1].labels).toHaveLength(1);
    expect(result[1].labels[0].text).toBe("Munich");
  });

  it("preserves non-svg labels on provinces", () => {
    const generatedLabel: Label = {
      text: "Generated",
      position: { x: 50, y: 50 },
      source: "generated",
    };
    const provinces: Province[] = [createProvince("ber", 100, 100, [generatedLabel])];
    const textElements: TextElement[] = [createTextElement("Berlin", 100, 100)];
    const associations = new Map<number, string | null>([[0, "ber"]]);

    const result = syncAssociationsToProvinces(
      textElements,
      provinces,
      associations
    );

    expect(result[0].labels).toHaveLength(2);
    expect(result[0].labels.find((l) => l.source === "generated")).toBeDefined();
    expect(result[0].labels.find((l) => l.source === "svg")).toBeDefined();
  });

  it("removes old svg labels when syncing", () => {
    const oldSvgLabel: Label = {
      text: "Old",
      position: { x: 10, y: 10 },
      source: "svg",
    };
    const provinces: Province[] = [createProvince("ber", 100, 100, [oldSvgLabel])];
    const textElements: TextElement[] = [createTextElement("New", 100, 100)];
    const associations = new Map<number, string | null>([[0, "ber"]]);

    const result = syncAssociationsToProvinces(
      textElements,
      provinces,
      associations
    );

    expect(result[0].labels).toHaveLength(1);
    expect(result[0].labels[0].text).toBe("New");
  });

  it("handles null associations (decorative text)", () => {
    const textElements: TextElement[] = [createTextElement("Decorative", 500, 500)];
    const provinces: Province[] = [createProvince("ber", 100, 100)];
    const associations = new Map<number, string | null>([[0, null]]);

    const result = syncAssociationsToProvinces(
      textElements,
      provinces,
      associations
    );

    expect(result[0].labels).toHaveLength(0);
  });

  it("handles multiple texts on same province", () => {
    const textElements: TextElement[] = [
      createTextElement("Spain", 100, 100),
      createTextElement("NC", 100, 120),
    ];
    const provinces: Province[] = [createProvince("spa", 100, 110)];
    const associations = new Map<number, string | null>([
      [0, "spa"],
      [1, "spa"],
    ]);

    const result = syncAssociationsToProvinces(
      textElements,
      provinces,
      associations
    );

    expect(result[0].labels).toHaveLength(2);
    expect(result[0].labels[0].text).toBe("Spain");
    expect(result[0].labels[1].text).toBe("NC");
  });
});

describe("buildAssociationsFromProvinces", () => {
  it("builds associations from existing province labels", () => {
    const textElements: TextElement[] = [
      createTextElement("Berlin", 100, 100),
      createTextElement("Munich", 200, 200),
    ];
    const berLabel: Label = {
      text: "Berlin",
      position: { x: 100, y: 100 },
      source: "svg",
    };
    const provinces: Province[] = [
      createProvince("ber", 100, 100, [berLabel]),
      createProvince("mun", 200, 200),
    ];

    const result = buildAssociationsFromProvinces(textElements, provinces);

    expect(result.get(0)).toBe("ber");
    expect(result.get(1)).toBeNull();
  });

  it("ignores generated labels", () => {
    const textElements: TextElement[] = [createTextElement("Berlin", 100, 100)];
    const generatedLabel: Label = {
      text: "Berlin",
      position: { x: 100, y: 100 },
      source: "generated",
    };
    const provinces: Province[] = [createProvince("ber", 100, 100, [generatedLabel])];

    const result = buildAssociationsFromProvinces(textElements, provinces);

    expect(result.get(0)).toBeNull();
  });

  it("initializes all text indices with null", () => {
    const textElements: TextElement[] = [
      createTextElement("A", 0, 0),
      createTextElement("B", 10, 10),
      createTextElement("C", 20, 20),
    ];
    const provinces: Province[] = [createProvince("ber", 100, 100)];

    const result = buildAssociationsFromProvinces(textElements, provinces);

    expect(result.size).toBe(3);
    expect(result.get(0)).toBeNull();
    expect(result.get(1)).toBeNull();
    expect(result.get(2)).toBeNull();
  });
});
