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
  if (name.includes("/")) return findLayerByPath(doc, name);
  const allGroups = Array.from(doc.getElementsByTagName("g"));
  return (
    allGroups.find((g) => g.getAttribute("inkscape:label") === name) ??
    allGroups.find((g) => g.getAttribute("id") === name) ??
    null
  );
}

function findLayerByPath(doc: Document, path: string): Element | null {
  const parts = path.split("/");
  let current: Element = doc.documentElement;
  for (const part of parts) {
    const found = Array.from(current.children).find(
      (child) => child.tagName.toLowerCase() === "g" && getLayerName(child) === part
    );
    if (!found) return null;
    current = found;
  }
  return current === doc.documentElement ? null : current;
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

  return { valid: true };
}

export interface SvgLayer {
  name: string;
  path: string;
  children: SvgLayer[];
}

export function extractLayerTree(svgString: string): SvgLayer[] {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgString, "image/svg+xml");
  return buildLayerChildren(doc.documentElement, null);
}

function buildLayerChildren(parent: Element, parentPath: string | null): SvgLayer[] {
  const result: SvgLayer[] = [];
  Array.from(parent.children).forEach((child) => {
    if (!isUserNamedLayer(child)) return;
    const name = getLayerName(child);
    if (!name) return;
    const path = parentPath ? `${parentPath}/${name}` : name;
    result.push({ name, path, children: buildLayerChildren(child, path) });
  });
  return result;
}

export function flattenLayerTree(layers: SvgLayer[]): SvgLayer[] {
  const result: SvgLayer[] = [];
  function traverse(layer: SvgLayer) {
    result.push(layer);
    layer.children.forEach(traverse);
  }
  layers.forEach(traverse);
  return result;
}

export function extractLayerNames(svgString: string): string[] {
  return flattenLayerTree(extractLayerTree(svgString)).map((l) => l.path);
}

export interface LayerNameMapping {
  provinces?: string;
  text?: string;
  namedCoasts?: string;
}

export function parseTextLayer(svgString: string, layerName: string): TextElement[] {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgString, "image/svg+xml");
  const layer = findLayerByName(doc, layerName);
  return extractTextElements(layer);
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

function circleToPath(el: Element): string {
  const cx = parseFloat(el.getAttribute("cx") ?? "0");
  const cy = parseFloat(el.getAttribute("cy") ?? "0");
  const r = parseFloat(el.getAttribute("r") ?? "0");
  return `M ${cx - r},${cy} a ${r},${r} 0 1,0 ${r * 2},0 a ${r},${r} 0 1,0 ${-r * 2},0 Z`;
}

function ellipseToPath(el: Element): string {
  const cx = parseFloat(el.getAttribute("cx") ?? "0");
  const cy = parseFloat(el.getAttribute("cy") ?? "0");
  const rx = parseFloat(el.getAttribute("rx") ?? "0");
  const ry = parseFloat(el.getAttribute("ry") ?? "0");
  return `M ${cx - rx},${cy} a ${rx},${ry} 0 1,0 ${rx * 2},0 a ${rx},${ry} 0 1,0 ${-rx * 2},0 Z`;
}

function rectToPath(el: Element): string {
  const x = parseFloat(el.getAttribute("x") ?? "0");
  const y = parseFloat(el.getAttribute("y") ?? "0");
  const w = parseFloat(el.getAttribute("width") ?? "0");
  const h = parseFloat(el.getAttribute("height") ?? "0");
  return `M ${x},${y} H ${x + w} V ${y + h} H ${x} Z`;
}

function elementToProvincePath(el: Element): ProvincePath | null {
  const tag = el.tagName.toLowerCase();
  let d: string;
  if (tag === "path") {
    d = el.getAttribute("d") ?? "";
  } else if (tag === "circle") {
    d = circleToPath(el);
  } else if (tag === "ellipse") {
    d = ellipseToPath(el);
  } else if (tag === "rect") {
    d = rectToPath(el);
  } else {
    return null;
  }
  return {
    elementId: el.getAttribute("id"),
    d,
    fill: el.getAttribute("fill"),
  };
}

function extractProvincePaths(provincesLayer: Element): ProvincePath[] {
  const elements = provincesLayer.querySelectorAll("path, circle, ellipse, rect");
  return Array.from(elements)
    .map(elementToProvincePath)
    .filter((p): p is ProvincePath => p !== null);
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

function extractDecorativeLayers(
  doc: Document,
  excludeLayerNames: string[]
): DecorativeElement[] {
  const svg = doc.documentElement;
  const result: DecorativeElement[] = [];
  let unnamedIndex = 0;

  Array.from(svg.children).forEach((child) => {
    if (child.tagName.toLowerCase() !== "g") return;
    const name = getLayerName(child);
    if (name && excludeLayerNames.includes(name)) return;

    if (!name) {
      result.push({
        id: `decorative_${unnamedIndex++}`,
        type: "group",
        content: child.innerHTML,
        children: [],
        styles: {},
      });
    } else {
      result.push(extractNamedDecorativeGroup(child, null));
    }
  });

  return result;
}

function isInkscapeDocument(doc: Document): boolean {
  const attrs = doc.documentElement.attributes;
  for (let i = 0; i < attrs.length; i++) {
    if (attrs[i].value === "http://www.inkscape.org/namespaces/inkscape") return true;
  }
  return false;
}

function isUserNamedLayer(element: Element): boolean {
  if (element.tagName.toLowerCase() !== "g") return false;
  // Inkscape marks every user layer with inkscape:groupmode="layer"
  if (element.getAttribute("inkscape:groupmode") === "layer") return true;
  // Belt-and-suspenders: also accept explicit inkscape:label
  if (element.getAttribute("inkscape:label") !== null) return true;
  // For non-Inkscape SVGs (Figma, Illustrator, etc.) any id-named group is a user layer
  const doc = element.ownerDocument;
  if (doc && !isInkscapeDocument(doc)) {
    return element.getAttribute("id") !== null;
  }
  return false;
}

function extractNamedDecorativeGroup(
  element: Element,
  parentPath: string | null
): DecorativeElement {
  const name = getLayerName(element)!;
  const path = parentPath ? `${parentPath}/${name}` : name;

  const children: DecorativeElement[] = [];
  Array.from(element.children).forEach((child) => {
    if (isUserNamedLayer(child)) {
      children.push(extractNamedDecorativeGroup(child, path));
    }
  });

  const content = Array.from(element.children)
    .filter((child) => !isUserNamedLayer(child))
    .map((child) => child.outerHTML)
    .join("");

  return { id: path, type: "group", content, children, styles: {} };
}

export function parseSvg(svgString: string, mapping?: LayerNameMapping): ParsedSvg {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgString, "image/svg+xml");
  const svg = doc.documentElement as unknown as SVGSVGElement;

  const dimensions = extractDimensions(svg);

  const provincesLayerName = mapping?.provinces ?? "provinces";
  const textLayerName = mapping?.text ?? "text";
  const coastsLayerName = mapping?.namedCoasts ?? "named-coasts";

  const provincesLayer = findLayerByName(doc, provincesLayerName);
  const provincePaths = provincesLayer
    ? extractProvincePaths(provincesLayer)
    : [];

  const coastsLayer = findLayerByName(doc, coastsLayerName);
  const coastPaths = extractCoastPaths(coastsLayer);

  const textLayer = findLayerByName(doc, textLayerName);
  const textElements = extractTextElements(textLayer);

  const decorativeElements = extractDecorativeLayers(doc, [
    provincesLayerName,
    coastsLayerName,
    textLayerName,
  ]);

  return {
    dimensions,
    provincePaths,
    coastPaths,
    textElements,
    decorativeElements,
  };
}
