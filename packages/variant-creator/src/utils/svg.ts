import type { SvgValidationResult } from "@/types/svg";
import type {
  ParsedSvg,
  ProvincePath,
  CoastPath,
  TextElement,
  DecorativeElement,
  Dimensions,
} from "@/types/variant";

export function findLayerByName(doc: Document, name: string): Element | null {
  const byLabel = doc.querySelector(`g[inkscape\\:label="${name}"]`);
  if (byLabel) return byLabel;

  return doc.querySelector(`g[id="${name}"]`);
}

export function validateSvg(svgString: string): SvgValidationResult {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgString, "image/svg+xml");

  const parseError = doc.querySelector("parsererror");
  if (parseError) {
    return {
      valid: false,
      error: { code: "INVALID_XML", message: "File is not valid XML" },
    };
  }

  const root = doc.documentElement;
  if (root.tagName.toLowerCase() !== "svg") {
    return {
      valid: false,
      error: { code: "NOT_SVG", message: "File is not an SVG document" },
    };
  }

  const provincesLayer = findLayerByName(doc, "provinces");
  if (!provincesLayer) {
    return {
      valid: false,
      error: {
        code: "MISSING_PROVINCES_LAYER",
        message: "SVG must contain a layer named 'provinces'",
      },
    };
  }

  const paths = provincesLayer.querySelectorAll("path");
  if (paths.length === 0) {
    return {
      valid: false,
      error: {
        code: "EMPTY_PROVINCES_LAYER",
        message: "Provinces layer must contain at least one path element",
      },
    };
  }

  return { valid: true };
}

function extractDimensions(svg: SVGSVGElement): Dimensions {
  const viewBox = svg.getAttribute("viewBox");
  if (viewBox) {
    const parts = viewBox.split(/\s+/).map(Number);
    if (parts.length >= 4) {
      return { width: parts[2], height: parts[3] };
    }
  }

  const width = parseFloat(svg.getAttribute("width") ?? "1000");
  const height = parseFloat(svg.getAttribute("height") ?? "1000");
  return { width, height };
}

function extractProvincePaths(provincesLayer: Element): ProvincePath[] {
  const paths = provincesLayer.querySelectorAll("path");
  return Array.from(paths).map(path => ({
    elementId: path.getAttribute("id"),
    d: path.getAttribute("d") ?? "",
    fill: path.getAttribute("fill"),
  }));
}

function extractCoastPaths(coastsLayer: Element | null): CoastPath[] {
  if (!coastsLayer) return [];

  const paths = coastsLayer.querySelectorAll("path");
  return Array.from(paths).map(path => ({
    elementId: path.getAttribute("id"),
    d: path.getAttribute("d") ?? "",
  }));
}

function extractTextStyles(
  text: SVGTextElement
): TextElement["styles"] | undefined {
  const computedStyle = text.getAttribute("style");
  const styles: TextElement["styles"] = {};

  const fontSize =
    text.getAttribute("font-size") ?? extractStyleProperty(computedStyle, "font-size");
  const fontFamily =
    text.getAttribute("font-family") ?? extractStyleProperty(computedStyle, "font-family");
  const fontWeight =
    text.getAttribute("font-weight") ?? extractStyleProperty(computedStyle, "font-weight");
  const fill =
    text.getAttribute("fill") ?? extractStyleProperty(computedStyle, "fill");

  if (fontSize) styles.fontSize = fontSize;
  if (fontFamily) styles.fontFamily = fontFamily;
  if (fontWeight) styles.fontWeight = fontWeight;
  if (fill) styles.fill = fill;

  return Object.keys(styles).length > 0 ? styles : undefined;
}

function extractStyleProperty(
  style: string | null,
  property: string
): string | undefined {
  if (!style) return undefined;
  const regex = new RegExp(`${property}\\s*:\\s*([^;]+)`);
  const match = style.match(regex);
  return match?.[1]?.trim();
}

function extractTextRotation(text: SVGTextElement): number | undefined {
  const transform = text.getAttribute("transform");
  if (!transform) return undefined;

  const rotateMatch = transform.match(/rotate\(([^)]+)\)/);
  if (rotateMatch) {
    const parts = rotateMatch[1].split(/[\s,]+/).map(Number);
    return parts[0];
  }
  return undefined;
}

function extractTextElements(textLayer: Element | null): TextElement[] {
  if (!textLayer) return [];

  const texts = textLayer.querySelectorAll("text");
  return Array.from(texts).map(text => {
    const firstTspan = text.querySelector("tspan");
    const x = text.getAttribute("x") ?? firstTspan?.getAttribute("x") ?? "0";
    const y = text.getAttribute("y") ?? firstTspan?.getAttribute("y") ?? "0";

    return {
      content: text.textContent ?? "",
      x: parseFloat(x),
      y: parseFloat(y),
      rotation: extractTextRotation(text),
      styles: extractTextStyles(text),
    };
  });
}

function getLayerName(group: Element): string | null {
  return (
    group.getAttribute("inkscape:label") ?? group.getAttribute("id") ?? null
  );
}

function serializeGroupContent(group: Element): string {
  return group.innerHTML;
}

function extractDecorativeLayers(
  doc: Document,
  excludeLayerNames: string[]
): DecorativeElement[] {
  const svg = doc.documentElement;
  const decorative: DecorativeElement[] = [];

  Array.from(svg.children).forEach((child, index) => {
    if (child.tagName.toLowerCase() !== "g") return;

    const name = getLayerName(child);
    if (name && excludeLayerNames.includes(name)) return;

    decorative.push({
      id: name ?? `decorative_${index}`,
      type: "group",
      content: serializeGroupContent(child),
      styles: {},
    });
  });

  return decorative;
}

export function parseSvg(svgString: string): ParsedSvg {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgString, "image/svg+xml");
  const svg = doc.documentElement as unknown as SVGSVGElement;

  const dimensions = extractDimensions(svg);

  const provincesLayer = findLayerByName(doc, "provinces");
  const provincePaths = provincesLayer
    ? extractProvincePaths(provincesLayer)
    : [];

  const coastsLayer = findLayerByName(doc, "named-coasts");
  const coastPaths = extractCoastPaths(coastsLayer);

  const textLayer = findLayerByName(doc, "text");
  const textElements = extractTextElements(textLayer);

  const decorativeElements = extractDecorativeLayers(doc, [
    "provinces",
    "named-coasts",
    "text",
  ]);

  return {
    dimensions,
    provincePaths,
    coastPaths,
    textElements,
    decorativeElements,
  };
}
