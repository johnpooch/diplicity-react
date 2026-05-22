export type Point = { x: number; y: number };

export type ViewBox = {
  minX: number;
  minY: number;
  width: number;
  height: number;
};

export type ParsedDsvg = {
  viewBox: ViewBox;
  rootFill: string | null;
  defs: string;
  background: string;
  provinceNames: string;
  borders: string;
  foreground: string;
  provincePaths: Map<string, string>;
  namedCoastPaths: Map<string, string>;
  unitPositions: Map<string, Point>;
  supplyCenters: Map<string, Point>;
};

const findLayer = (root: Element, id: string): Element | null => {
  for (const child of Array.from(root.children)) {
    if (child.tagName.toLowerCase() === "g" && child.getAttribute("id") === id) {
      return child;
    }
  }
  return null;
};

const parseViewBox = (root: Element): ViewBox => {
  const raw = root.getAttribute("viewBox");
  if (!raw) {
    throw new Error("dSVG is missing a viewBox");
  }
  const parts = raw.trim().split(/[\s,]+/).map(Number);
  if (parts.length !== 4 || parts.some(Number.isNaN)) {
    throw new Error(`dSVG has an invalid viewBox: "${raw}"`);
  }
  const [minX, minY, width, height] = parts;
  return { minX, minY, width, height };
};

const collectPaths = (layer: Element | null): Map<string, string> => {
  const paths = new Map<string, string>();
  if (!layer) {
    return paths;
  }
  for (const path of Array.from(layer.querySelectorAll("path"))) {
    const id = path.getAttribute("id");
    const d = path.getAttribute("d");
    if (id && d) {
      paths.set(id, d);
    }
  }
  return paths;
};

const collectPoints = (layer: Element | null): Map<string, Point> => {
  const points = new Map<string, Point>();
  if (!layer) {
    return points;
  }
  for (const circle of Array.from(layer.querySelectorAll("circle"))) {
    const id = circle.getAttribute("id");
    const cx = circle.getAttribute("cx");
    const cy = circle.getAttribute("cy");
    if (id && cx !== null && cy !== null) {
      points.set(id, { x: Number(cx), y: Number(cy) });
    }
  }
  return points;
};

const stripRedundantNamespace = (markup: string): string =>
  markup.split(' xmlns="http://www.w3.org/2000/svg"').join("");

const collectDefs = (root: Element): string => {
  let markup = "";
  for (const child of Array.from(root.children)) {
    const tag = child.tagName.toLowerCase();
    if (tag === "defs" || tag === "style") {
      markup += child.outerHTML;
    }
  }
  return stripRedundantNamespace(markup);
};

const layerMarkup = (root: Element, id: string): string =>
  stripRedundantNamespace(findLayer(root, id)?.innerHTML ?? "");

export const parseDsvg = (svg: string): ParsedDsvg => {
  const doc = new DOMParser().parseFromString(svg, "image/svg+xml");
  const parseError = doc.querySelector("parsererror");
  if (parseError) {
    throw new Error(
      `dSVG is not well-formed XML: ${parseError.textContent ?? ""}`.trim()
    );
  }
  const root = doc.documentElement;
  if (root.tagName.toLowerCase() !== "svg") {
    throw new Error("dSVG root element is not <svg>");
  }

  return {
    viewBox: parseViewBox(root),
    rootFill: root.getAttribute("fill"),
    defs: collectDefs(root),
    background: layerMarkup(root, "background"),
    provinceNames: layerMarkup(root, "province-names"),
    borders: layerMarkup(root, "borders"),
    foreground: layerMarkup(root, "foreground"),
    provincePaths: collectPaths(findLayer(root, "provinces")),
    namedCoastPaths: collectPaths(findLayer(root, "named-coasts")),
    unitPositions: collectPoints(findLayer(root, "unit-positions")),
    supplyCenters: collectPoints(findLayer(root, "supply-centers")),
  };
};
