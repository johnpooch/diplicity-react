export interface ProvinceElement {
  svgId: string;
  pathData: string[];
}

function collectPathData(el: Element): string[] {
  const paths: string[] = [];
  const d = el.getAttribute("d");
  if (d) paths.push(d);
  Array.from(el.children).forEach(child => paths.push(...collectPathData(child)));
  return paths;
}

export interface ExtractedProvinces {
  viewBox: string;
  provinces: ProvinceElement[];
}

export function extractLayerPaths(
  svgContent: string,
  layerKey: string | null
): string[] {
  if (!layerKey) return [];

  const parser = new DOMParser();
  const doc = parser.parseFromString(svgContent, "image/svg+xml");
  const root = doc.documentElement;

  const path = layerKey.replace(/^root-/, "").split("-").map(Number);
  let el: Element = root;
  for (const index of path) {
    const child = el.children[index];
    if (!child) return [];
    el = child;
  }

  const paths: string[] = [];
  const collect = (element: Element) => {
    const d = element.getAttribute("d");
    if (d) paths.push(d);
    Array.from(element.children).forEach(collect);
  };
  Array.from(el.children).forEach(collect);

  return paths;
}

export function extractProvinces(
  svgContent: string,
  provincesKey: string | null
): ExtractedProvinces {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgContent, "image/svg+xml");
  const root = doc.documentElement;

  const viewBox = root.getAttribute("viewBox") ?? "0 0 1000 1000";

  if (!provincesKey) return { viewBox, provinces: [] };

  const path = provincesKey
    .replace(/^root-/, "")
    .split("-")
    .map(Number);

  let el: Element = root;
  for (const index of path) {
    const child = el.children[index];
    if (!child) return { viewBox, provinces: [] };
    el = child;
  }

  const provinces: ProvinceElement[] = [];
  Array.from(el.children).forEach(child => {
    const id = child.getAttribute("id");
    if (!id) return;
    provinces.push({ svgId: id, pathData: collectPathData(child) });
  });

  return { viewBox, provinces };
}
