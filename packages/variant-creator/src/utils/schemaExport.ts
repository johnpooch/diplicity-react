import type { VariantDefinition, Province, NamedCoast, DecorativeElement } from "@/types/variant";

type PhaseType = "Movement" | "Retreat" | "Adjustment";

interface SchemaPosition {
  x: number;
  y: number;
}

interface SchemaLabel {
  text: string;
  position: SchemaPosition;
  rotation?: number;
  source: "svg" | "generated";
  style?: Record<string, unknown>;
}

interface SchemaAdjacency {
  to: string;
  pass: "army" | "fleet" | "both";
}

interface SchemaProvince {
  id: string;
  name: string;
  type: "land" | "sea" | "coastal";
  supplyCenter: boolean;
  homeNation?: string;
  adjacencies: SchemaAdjacency[];
  path: string;
  labels: SchemaLabel[];
  unitPosition: SchemaPosition;
  dislodgedUnitPosition: SchemaPosition;
  supplyCenterPosition?: SchemaPosition;
}

interface SchemaNamedCoast {
  id: string;
  name: string;
  parentProvince: string;
  adjacencies: SchemaAdjacency[];
  path: string;
  unitPosition: SchemaPosition;
  dislodgedUnitPosition: SchemaPosition;
}

interface SchemaNation {
  id: string;
  name: string;
  color: string;
}

interface PhaseTransition {
  from: { season: string; type: PhaseType };
  to: { season: string; type: PhaseType; yearDelta: number };
}

interface SchemaPhaseProgression {
  seasons: string[];
  transitions: PhaseTransition[];
}

interface SchemaUnit {
  nation: string;
  type: "Army" | "Fleet";
  location: string;
}

interface SchemaSupplyCenter {
  nation: string;
  province: string;
}

interface SchemaInitialState {
  phase: { season: string; year: number; type: PhaseType };
  units: SchemaUnit[];
  supplyCenters: SchemaSupplyCenter[];
}

type SchemaDecorativeElement =
  | { kind: "path"; d: string; fill?: string; stroke?: string; strokeWidth?: number }
  | { kind: "text"; text: string; position: SchemaPosition; rotation?: number; style?: Record<string, unknown> }
  | { kind: "group"; id?: string; children: SchemaDecorativeElement[] };

interface SchemaTextElement {
  text: string;
  position: SchemaPosition;
  rotation?: number;
  style?: Record<string, unknown>;
}

export interface SchemaVariant {
  schemaVersion: 1;
  id: string;
  name: string;
  description: string;
  author: string;
  soloVictorySupplyCenters: number;
  phaseProgression: SchemaPhaseProgression;
  nations: SchemaNation[];
  provinces: SchemaProvince[];
  namedCoasts: SchemaNamedCoast[];
  initialState: SchemaInitialState;
  dimensions: { width: number; height: number };
  decorativeElements: SchemaDecorativeElement[];
  textElements?: SchemaTextElement[];
}

const DEFAULT_PHASE_PROGRESSION: SchemaPhaseProgression = {
  seasons: ["Spring", "Fall"],
  transitions: [
    { from: { season: "Spring", type: "Movement" }, to: { season: "Spring", type: "Retreat", yearDelta: 0 } },
    { from: { season: "Spring", type: "Retreat" }, to: { season: "Fall", type: "Movement", yearDelta: 0 } },
    { from: { season: "Fall", type: "Movement" }, to: { season: "Fall", type: "Retreat", yearDelta: 0 } },
    { from: { season: "Fall", type: "Retreat" }, to: { season: "Fall", type: "Adjustment", yearDelta: 0 } },
    { from: { season: "Fall", type: "Adjustment" }, to: { season: "Spring", type: "Movement", yearDelta: 1 } },
  ],
};

function toKebabId(name: string): string {
  return name
    .trim()
    .toLowerCase()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "")
    .replace(/^-+|-+$/g, "");
}

type InternalProvinceType = "land" | "sea" | "coastal" | "namedCoasts";

function inferPass(fromType: InternalProvinceType, toType: InternalProvinceType): "army" | "fleet" | "both" {
  if (fromType === "sea" || toType === "sea") return "fleet";
  if (fromType === "coastal" && toType === "coastal") return "both";
  return "army";
}

function convertAdjacencies(province: Province, allProvinces: Province[]): SchemaAdjacency[] {
  return province.adjacencies.map((toId) => {
    if (toId.includes("/")) {
      return { to: toId, pass: "fleet" as const };
    }
    const target = allProvinces.find((p) => p.id === toId);
    if (!target) return { to: toId, pass: "army" as const };
    return { to: toId, pass: inferPass(province.type, target.type) };
  });
}

function convertNamedCoastAdjacencies(namedCoast: NamedCoast): SchemaAdjacency[] {
  return namedCoast.adjacencies.map((toId) => ({ to: toId, pass: "fleet" as const }));
}

function convertLabels(province: Province): SchemaLabel[] {
  return province.labels.map((label) => {
    const result: SchemaLabel = {
      text: label.text,
      position: label.position,
      source: label.source,
    };
    if (label.rotation !== undefined) result.rotation = label.rotation;
    if (label.styles) result.style = { ...label.styles };
    return result;
  });
}

function convertProvince(province: Province, allProvinces: Province[]): SchemaProvince {
  const schemaType: "land" | "sea" | "coastal" =
    province.type === "namedCoasts" ? "land" : province.type;

  const result: SchemaProvince = {
    id: province.id,
    name: province.name,
    type: schemaType,
    supplyCenter: province.supplyCenter,
    adjacencies: convertAdjacencies(province, allProvinces),
    path: province.path,
    labels: convertLabels(province),
    unitPosition: province.unitPosition,
    dislodgedUnitPosition: province.dislodgedUnitPosition,
  };

  if (province.homeNation !== null) result.homeNation = province.homeNation;
  if (province.supplyCenter && province.supplyCenterPosition) {
    result.supplyCenterPosition = province.supplyCenterPosition;
  }

  return result;
}

function convertNamedCoast(namedCoast: NamedCoast): SchemaNamedCoast {
  return {
    id: namedCoast.id,
    name: namedCoast.name,
    parentProvince: namedCoast.parentId,
    adjacencies: convertNamedCoastAdjacencies(namedCoast),
    path: namedCoast.path,
    unitPosition: namedCoast.unitPosition,
    dislodgedUnitPosition: namedCoast.dislodgedUnitPosition,
  };
}

function extractDecorativeChildren(element: Element): SchemaDecorativeElement[] {
  const result: SchemaDecorativeElement[] = [];
  Array.from(element.children).forEach((child) => {
    const tag = child.tagName.toLowerCase();
    if (tag === "path") {
      const d = child.getAttribute("d");
      if (!d) return;
      const fill = child.getAttribute("fill") ?? undefined;
      const stroke = child.getAttribute("stroke") ?? undefined;
      const strokeWidthStr = child.getAttribute("stroke-width");
      const strokeWidth = strokeWidthStr !== null ? parseFloat(strokeWidthStr) : undefined;
      result.push({ kind: "path", d, fill, stroke, strokeWidth });
    } else if (tag === "g") {
      result.push({
        kind: "group",
        id: child.getAttribute("id") ?? undefined,
        children: extractDecorativeChildren(child),
      });
    } else if (tag === "text") {
      const x = parseFloat(child.getAttribute("x") ?? "0");
      const y = parseFloat(child.getAttribute("y") ?? "0");
      result.push({ kind: "text", text: child.textContent ?? "", position: { x, y } });
    }
  });
  return result;
}

function convertDecorativeElement(element: DecorativeElement): SchemaDecorativeElement {
  const contentChildren: SchemaDecorativeElement[] = [];
  if (element.content) {
    const parser = new DOMParser();
    const doc = parser.parseFromString(`<svg>${element.content}</svg>`, "image/svg+xml");
    contentChildren.push(...extractDecorativeChildren(doc.documentElement));
  }
  const subgroupChildren = (element.children ?? []).map(convertDecorativeElement);
  return {
    kind: "group",
    id: element.id,
    children: [...contentChildren, ...subgroupChildren],
  };
}

function buildInitialState(variant: VariantDefinition): SchemaInitialState {
  const units: SchemaUnit[] = [];
  const supplyCenters: SchemaSupplyCenter[] = [];

  for (const province of variant.provinces) {
    if (province.startingUnit && province.homeNation) {
      units.push({
        nation: province.homeNation,
        type: province.startingUnit.type,
        location: province.id,
      });
    }
    if (province.supplyCenter && province.homeNation) {
      supplyCenters.push({ nation: province.homeNation, province: province.id });
    }
  }

  return {
    phase: { season: "Spring", year: variant.startYear, type: "Movement" },
    units,
    supplyCenters,
  };
}

export function toSchemaVariant(variant: VariantDefinition): SchemaVariant {
  const id = toKebabId(variant.name) || "my-variant";
  const textElements = variant.textElements.map((t) => ({
    text: t.content,
    position: { x: t.x, y: t.y },
    ...(t.rotation !== undefined ? { rotation: t.rotation } : {}),
    ...(t.styles ? { style: { ...t.styles } } : {}),
  }));

  return {
    schemaVersion: 1,
    id,
    name: variant.name,
    description: variant.description,
    author: variant.author,
    soloVictorySupplyCenters: variant.soloVictorySCCount,
    phaseProgression: DEFAULT_PHASE_PROGRESSION,
    nations: variant.nations.map((n) => ({ id: n.id, name: n.name, color: n.color })),
    provinces: variant.provinces.map((p) => convertProvince(p, variant.provinces)),
    namedCoasts: variant.namedCoasts.map(convertNamedCoast),
    initialState: buildInitialState(variant),
    dimensions: variant.dimensions,
    decorativeElements: variant.decorativeElements.map(convertDecorativeElement),
    ...(textElements.length > 0 ? { textElements } : {}),
  };
}

export function downloadSchemaJson(variant: VariantDefinition): void {
  const schema = toSchemaVariant(variant);
  const json = JSON.stringify(schema, null, 2);
  const blob = new Blob([json], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${schema.id}.json`;
  a.click();
  URL.revokeObjectURL(url);
}
