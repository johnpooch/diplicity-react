import type { SvgValidationResult } from "@/types/svg";

function findLayerByName(doc: Document, name: string): Element | null {
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
