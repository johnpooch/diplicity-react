import type { LayerAssignments } from "@/components/dsvg/LayerAssignment";

function filterGroups(
  el: Element,
  currentPath: number[],
  assignedPaths: number[][]
): void {
  Array.from(el.children).forEach((child, i) => {
    const tag = child.tagName.toLowerCase();
    if (tag === "defs" || tag === "style" || tag === "metadata") return;
    if (tag !== "g") return;

    const childPath = [...currentPath, i];

    const isAssigned = assignedPaths.some(
      ap =>
        ap.length === childPath.length &&
        ap.every((v, idx) => v === childPath[idx])
    );
    const isAncestor = assignedPaths.some(
      ap =>
        ap.length > childPath.length &&
        childPath.every((v, idx) => v === ap[idx])
    );

    if (isAssigned) {
      // keep this element and all descendants — no action needed
    } else if (isAncestor) {
      filterGroups(child, childPath, assignedPaths);
    } else {
      child.setAttribute("display", "none");
    }
  });
}

export function buildPreviewSvg(
  svgContent: string,
  assignments: LayerAssignments
): string {
  const assignedKeys = [
    assignments.provinces,
    assignments.namedCoasts,
    assignments.provinceNames,
    assignments.borders,
  ].filter((k): k is string => k !== null);

  if (assignedKeys.length === 0) return svgContent;

  const assignedPaths = assignedKeys.map(key =>
    key
      .replace(/^root-/, "")
      .split("-")
      .map(Number)
  );

  const parser = new DOMParser();
  const doc = parser.parseFromString(svgContent, "image/svg+xml");

  filterGroups(doc.documentElement, [], assignedPaths);

  return new XMLSerializer().serializeToString(doc);
}
