import type { SvgTreeNode } from "@/utils/svgTree";
import type { LayerAssignments } from "@/components/dsvg/LayerAssignment";

const INKSCAPE_NS = "http://www.inkscape.org/namespaces/inkscape";
const SODIPODI_NS = "http://sodipodi.sourceforge.net/DTD/sodipodi-0.0.dtd";

function getElementByKey(root: Element, key: string): Element | null {
  const indices = key.replace(/^root-/, "").split("-").map(Number);
  let el: Element = root;
  for (const idx of indices) {
    const child = el.children[idx];
    if (!child) return null;
    el = child;
  }
  return el;
}

function makeLayerGroup(doc: Document, id: string, label: string): Element {
  const g = doc.createElementNS("http://www.w3.org/2000/svg", "g");
  g.setAttribute("id", id);
  g.setAttributeNS(INKSCAPE_NS, "inkscape:label", label);
  g.setAttributeNS(INKSCAPE_NS, "inkscape:groupmode", "layer");
  return g;
}

export function buildDsvgOutput(
  svgContent: string,
  assignments: LayerAssignments
): string {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgContent, "image/svg+xml");
  const root = doc.documentElement;

  if (!root.hasAttribute("xmlns:inkscape")) {
    root.setAttribute("xmlns:inkscape", INKSCAPE_NS);
  }
  if (!root.hasAttribute("xmlns:sodipodi")) {
    root.setAttribute("xmlns:sodipodi", SODIPODI_NS);
  }

  function cloneByKey(key: string | null): Element | null {
    if (!key) return null;
    const el = getElementByKey(root, key);
    return el ? (el.cloneNode(true) as Element) : null;
  }

  const provincesEl = cloneByKey(assignments.provinces);
  const namedCoastsEl = cloneByKey(assignments.namedCoasts);
  const provinceNamesEl = cloneByKey(assignments.provinceNames);
  const bordersEl = cloneByKey(assignments.borders);

  // Find background/foreground by navigating to provinces' parent and collecting
  // sibling <g> elements that are not one of the four assigned layers.
  const backgroundNodes: Element[] = [];
  const foregroundNodes: Element[] = [];

  if (assignments.provinces) {
    const provincesPath = assignments.provinces
      .replace(/^root-/, "")
      .split("-")
      .map(Number);
    const provincesLocalIdx = provincesPath[provincesPath.length - 1];
    const parentPath = provincesPath.slice(0, -1);

    let parentEl: Element = root;
    let navigated = true;
    for (const idx of parentPath) {
      const child = parentEl.children[idx];
      if (!child) {
        navigated = false;
        break;
      }
      parentEl = child;
    }

    if (navigated) {
      // Determine which local indices (within this parent) are assigned layers
      const assignedLocalIndices = new Set<number>();
      for (const key of [
        assignments.provinces,
        assignments.namedCoasts,
        assignments.provinceNames,
        assignments.borders,
      ]) {
        if (!key) continue;
        const kPath = key.replace(/^root-/, "").split("-").map(Number);
        if (kPath.length !== provincesPath.length) continue;
        const kParent = kPath.slice(0, -1);
        if (kParent.length !== parentPath.length) continue;
        if (!kParent.every((v, i) => v === parentPath[i])) continue;
        assignedLocalIndices.add(kPath[kPath.length - 1]);
      }

      Array.from(parentEl.children).forEach((child, i) => {
        if (child.tagName.toLowerCase() !== "g") return;
        if (assignedLocalIndices.has(i)) return;
        const clone = child.cloneNode(true) as Element;
        if (i < provincesLocalIdx) {
          backgroundNodes.push(clone);
        } else {
          foregroundNodes.push(clone);
        }
      });
    }
  }

  // Preserve non-<g> root children (defs, style, etc.)
  const headerNodes: Node[] = [];
  Array.from(root.childNodes).forEach(child => {
    if (child.nodeType !== Node.ELEMENT_NODE) {
      headerNodes.push(child.cloneNode(true));
    } else if ((child as Element).tagName.toLowerCase() !== "g") {
      headerNodes.push(child.cloneNode(true));
    }
  });

  while (root.firstChild) root.removeChild(root.firstChild);
  headerNodes.forEach(n => root.appendChild(n));

  // All six output layers are always emitted (empty if not assigned)

  const bg = makeLayerGroup(doc, "background", "background");
  backgroundNodes.forEach(el => bg.appendChild(el));
  root.appendChild(bg);

  const pLayer = provincesEl ?? makeLayerGroup(doc, "provinces", "provinces");
  pLayer.setAttribute("id", "provinces");
  pLayer.setAttributeNS(INKSCAPE_NS, "inkscape:label", "provinces");
  pLayer.setAttributeNS(INKSCAPE_NS, "inkscape:groupmode", "layer");
  pLayer.setAttribute("style", "display:none");
  pLayer.setAttributeNS(SODIPODI_NS, "sodipodi:insensitive", "true");
  root.appendChild(pLayer);

  const ncLayer = namedCoastsEl ?? makeLayerGroup(doc, "named-coasts", "named-coasts");
  ncLayer.setAttribute("id", "named-coasts");
  ncLayer.setAttributeNS(INKSCAPE_NS, "inkscape:label", "named-coasts");
  ncLayer.setAttributeNS(INKSCAPE_NS, "inkscape:groupmode", "layer");
  ncLayer.setAttribute("style", "display:none");
  ncLayer.setAttributeNS(SODIPODI_NS, "sodipodi:insensitive", "true");
  root.appendChild(ncLayer);

  const pnLayer = provinceNamesEl ?? makeLayerGroup(doc, "province-names", "province-names");
  pnLayer.setAttribute("id", "province-names");
  pnLayer.setAttributeNS(INKSCAPE_NS, "inkscape:label", "province-names");
  pnLayer.setAttributeNS(INKSCAPE_NS, "inkscape:groupmode", "layer");
  root.appendChild(pnLayer);

  const bLayer = bordersEl ?? makeLayerGroup(doc, "borders", "borders");
  bLayer.setAttribute("id", "borders");
  bLayer.setAttributeNS(INKSCAPE_NS, "inkscape:label", "borders");
  bLayer.setAttributeNS(INKSCAPE_NS, "inkscape:groupmode", "layer");
  root.appendChild(bLayer);

  const fg = makeLayerGroup(doc, "foreground", "foreground");
  foregroundNodes.forEach(el => fg.appendChild(el));
  root.appendChild(fg);

  return new XMLSerializer().serializeToString(doc);
}

export function buildVisibilityPreviewSvg(
  svgContent: string,
  nodes: SvgTreeNode[],
  visibleKeys: Set<string>
): string {
  const parser = new DOMParser();
  const doc = parser.parseFromString(svgContent, "image/svg+xml");
  const root = doc.documentElement;

  for (const node of nodes) {
    const el = getElementByKey(root, node.key);
    if (!el) continue;
    const style = el.getAttribute("style") ?? "";
    const cleaned = style.replace(/display\s*:\s*[^;]+;?\s*/g, "").trim();
    if (visibleKeys.has(node.key)) {
      if (cleaned) el.setAttribute("style", cleaned);
      else el.removeAttribute("style");
    } else {
      el.setAttribute("style", cleaned ? `${cleaned};display:none` : "display:none");
    }
  }

  return new XMLSerializer().serializeToString(doc);
}
