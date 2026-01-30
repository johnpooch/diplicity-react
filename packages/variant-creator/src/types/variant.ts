export interface Position {
  x: number;
  y: number;
}

export interface Label {
  text: string;
  position: Position;
  rotation?: number;
  source: "svg" | "generated";
  styles?: {
    fontSize?: string;
    fontFamily?: string;
    fontWeight?: string;
    fill?: string;
  };
}

export interface Province {
  id: string;
  elementId: string;
  name: string;
  type: "land" | "sea" | "coastal" | "namedCoasts";
  path: string;
  homeNation: string | null;
  supplyCenter: boolean;
  startingUnit: { type: "Army" | "Fleet" } | null;
  adjacencies: string[];
  labels: Label[];
  unitPosition: Position;
  dislodgedUnitPosition: Position;
  supplyCenterPosition?: Position;
}

export interface NamedCoast {
  id: string;
  name: string;
  parentId: string;
  path: string;
  adjacencies: string[];
  unitPosition: Position;
  dislodgedUnitPosition: Position;
}

export interface Nation {
  id: string;
  name: string;
  color: string;
}

export interface DecorativeElement {
  id: string;
  type: "path" | "text" | "group";
  content: string;
  styles?: Record<string, string>;
}

export interface Dimensions {
  width: number;
  height: number;
}

export interface VariantDefinition {
  name: string;
  description: string;
  author: string;
  version: string;
  soloVictorySCCount: number;
  nations: Nation[];
  provinces: Province[];
  namedCoasts: NamedCoast[];
  decorativeElements: DecorativeElement[];
  dimensions: Dimensions;
  textElements: TextElement[];
}

export interface ProvincePath {
  elementId: string | null;
  d: string;
  fill: string | null;
}

export interface CoastPath {
  elementId: string | null;
  d: string;
}

export interface TextElement {
  content: string;
  x: number;
  y: number;
  rotation?: number;
  styles?: {
    fontSize?: string;
    fontFamily?: string;
    fontWeight?: string;
    fill?: string;
  };
}

export interface ParsedSvg {
  dimensions: Dimensions;
  provincePaths: ProvincePath[];
  coastPaths: CoastPath[];
  textElements: TextElement[];
  decorativeElements: DecorativeElement[];
}
