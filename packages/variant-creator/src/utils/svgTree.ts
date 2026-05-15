export interface SvgTreeNode {
  key: string;
  name: string;
  isLayer: boolean;
  children: SvgTreeNode[];
  elementCount: number;
}

const SKIP_TAGS = new Set([
  "defs",
  "style",
  "script",
  "metadata",
  "title",
  "desc",
]);

function getGroupName(el: Element): string {
  return (
    el.getAttribute("inkscape:label") ??
    el.getAttribute("id") ??
    null
  );
}

function buildNode(el: Element, keyPrefix: string): SvgTreeNode {
  const rawName = getGroupName(el);
  const name = rawName ?? "(unnamed)";
  const isLayer = el.getAttribute("inkscape:groupmode") === "layer";

  const children: SvgTreeNode[] = [];
  let elementCount = 0;

  Array.from(el.children).forEach((child, i) => {
    const tag = child.tagName.toLowerCase();
    if (SKIP_TAGS.has(tag)) return;
    if (tag === "g") {
      children.push(buildNode(child, `${keyPrefix}-${i}`));
    } else {
      elementCount++;
    }
  });

  return { key: keyPrefix, name, isLayer, children, elementCount };
}

export function parseSvgTree(svgString: string): SvgTreeNode[] {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgString, "image/svg+xml");

  const root = doc.documentElement;
  const nodes: SvgTreeNode[] = [];

  Array.from(root.children).forEach((child, i) => {
    const tag = child.tagName.toLowerCase();
    if (SKIP_TAGS.has(tag)) return;
    if (tag === "g") {
      nodes.push(buildNode(child, `root-${i}`));
    }
  });

  return nodes;
}

export interface FlatSvgNode {
  key: string;
  name: string;
  breadcrumb: string;
  isLayer: boolean;
}

export function flattenTree(
  nodes: SvgTreeNode[],
  parentBreadcrumb = ""
): FlatSvgNode[] {
  const result: FlatSvgNode[] = [];
  for (const node of nodes) {
    const breadcrumb = parentBreadcrumb
      ? `${parentBreadcrumb} › ${node.name}`
      : node.name;
    result.push({ key: node.key, name: node.name, breadcrumb, isLayer: node.isLayer });
    result.push(...flattenTree(node.children, breadcrumb));
  }
  return result;
}

export function validateAnySvg(svgString: string): string | null {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgString, "image/svg+xml");

  if (doc.querySelector("parsererror")) return "File is not valid XML.";
  if (doc.documentElement.tagName.toLowerCase() !== "svg")
    return "File is not an SVG document.";

  return null;
}
