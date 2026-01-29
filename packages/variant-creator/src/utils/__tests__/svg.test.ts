import { describe, it, expect } from "vitest";
import { validateSvg, parseSvg } from "../svg";

describe("validateSvg", () => {
  it("returns valid for SVG with provinces layer containing paths (id attribute)", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <g id="provinces">
          <path id="ber" d="M10,10 L30,10 L30,30 L10,30 Z"/>
          <path id="mun" d="M40,10 L60,10 L60,30 L40,30 Z"/>
        </g>
      </svg>
    `;

    const result = validateSvg(svg);
    expect(result).toEqual({ valid: true });
  });

  it("returns valid for SVG with provinces layer using inkscape:label", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape" viewBox="0 0 100 100">
        <g inkscape:label="provinces">
          <path d="M10,10 L30,10 L30,30 L10,30 Z"/>
        </g>
      </svg>
    `;

    const result = validateSvg(svg);
    expect(result).toEqual({ valid: true });
  });

  it("returns MISSING_PROVINCES_LAYER error when provinces layer is missing", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <g id="background">
          <rect width="100" height="100" fill="blue"/>
        </g>
      </svg>
    `;

    const result = validateSvg(svg);
    expect(result).toEqual({
      valid: false,
      error: {
        code: "MISSING_PROVINCES_LAYER",
        message: "SVG must contain a layer named 'provinces'",
      },
    });
  });

  it("returns EMPTY_PROVINCES_LAYER error when provinces layer has no paths", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <g id="provinces">
        </g>
      </svg>
    `;

    const result = validateSvg(svg);
    expect(result).toEqual({
      valid: false,
      error: {
        code: "EMPTY_PROVINCES_LAYER",
        message: "Provinces layer must contain at least one path element",
      },
    });
  });

  it("returns INVALID_XML error for malformed XML", () => {
    const malformedXml = `
      <svg xmlns="http://www.w3.org/2000/svg">
        <g id="provinces">
          <path d="M10,10
        </g>
      </svg>
    `;

    const result = validateSvg(malformedXml);
    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.error.code).toBe("INVALID_XML");
    }
  });

  it("returns NOT_SVG error when root element is not svg", () => {
    const htmlDoc = `
      <html>
        <body>
          <g id="provinces">
            <path d="M10,10 L30,10 L30,30 L10,30 Z"/>
          </g>
        </body>
      </html>
    `;

    const result = validateSvg(htmlDoc);
    expect(result).toEqual({
      valid: false,
      error: {
        code: "NOT_SVG",
        message: "File is not an SVG document",
      },
    });
  });

  it("returns INVALID_XML error for plain text", () => {
    const plainText = "This is not XML at all";

    const result = validateSvg(plainText);
    expect(result.valid).toBe(false);
    if (!result.valid) {
      expect(result.error.code).toBe("INVALID_XML");
    }
  });

  it("returns EMPTY_PROVINCES_LAYER when provinces contains only non-path elements", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <g id="provinces">
          <rect width="100" height="100" fill="blue"/>
          <circle cx="50" cy="50" r="25"/>
        </g>
      </svg>
    `;

    const result = validateSvg(svg);
    expect(result).toEqual({
      valid: false,
      error: {
        code: "EMPTY_PROVINCES_LAYER",
        message: "Provinces layer must contain at least one path element",
      },
    });
  });
});

describe("parseSvg", () => {
  it("extracts correct number of provinces", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <g id="provinces">
          <path id="ber" d="M10,10 L30,10 L30,30 L10,30 Z"/>
          <path id="mun" d="M40,10 L60,10 L60,30 L40,30 Z"/>
          <path id="kie" d="M70,10 L90,10 L90,30 L70,30 Z"/>
        </g>
      </svg>
    `;

    const result = parseSvg(svg);
    expect(result.provincePaths).toHaveLength(3);
  });

  it("preserves province element IDs", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <g id="provinces">
          <path id="ber" d="M10,10 L30,10 L30,30 L10,30 Z"/>
          <path id="mun" d="M40,10 L60,10 L60,30 L40,30 Z"/>
        </g>
      </svg>
    `;

    const result = parseSvg(svg);
    expect(result.provincePaths[0].elementId).toBe("ber");
    expect(result.provincePaths[1].elementId).toBe("mun");
  });

  it("handles missing optional layers gracefully", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <g id="provinces">
          <path id="ber" d="M10,10 L30,10 L30,30 L10,30 Z"/>
        </g>
      </svg>
    `;

    const result = parseSvg(svg);
    expect(result.coastPaths).toHaveLength(0);
    expect(result.textElements).toHaveLength(0);
  });

  it("extracts text with positions", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <g id="provinces">
          <path id="ber" d="M10,10 L30,10 L30,30 L10,30 Z"/>
        </g>
        <g id="text">
          <text x="20" y="25">Berlin</text>
          <text x="50" y="55">Munich</text>
        </g>
      </svg>
    `;

    const result = parseSvg(svg);
    expect(result.textElements).toHaveLength(2);
    expect(result.textElements[0].content).toBe("Berlin");
    expect(result.textElements[0].x).toBe(20);
    expect(result.textElements[0].y).toBe(25);
    expect(result.textElements[1].content).toBe("Munich");
    expect(result.textElements[1].x).toBe(50);
    expect(result.textElements[1].y).toBe(55);
  });

  it("extracts dimensions from viewBox", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1524 1357">
        <g id="provinces">
          <path id="ber" d="M10,10 L30,10 L30,30 L10,30 Z"/>
        </g>
      </svg>
    `;

    const result = parseSvg(svg);
    expect(result.dimensions).toEqual({ width: 1524, height: 1357 });
  });

  it("extracts dimensions from width/height when no viewBox", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" width="800" height="600">
        <g id="provinces">
          <path id="ber" d="M10,10 L30,10 L30,30 L10,30 Z"/>
        </g>
      </svg>
    `;

    const result = parseSvg(svg);
    expect(result.dimensions).toEqual({ width: 800, height: 600 });
  });

  it("extracts coast paths from named-coasts layer", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <g id="provinces">
          <path id="stp" d="M10,10 L30,10 L30,30 L10,30 Z"/>
        </g>
        <g id="named-coasts">
          <path id="stp-nc" d="M10,10 L20,10"/>
          <path id="stp-sc" d="M20,30 L30,30"/>
        </g>
      </svg>
    `;

    const result = parseSvg(svg);
    expect(result.coastPaths).toHaveLength(2);
    expect(result.coastPaths[0].elementId).toBe("stp-nc");
    expect(result.coastPaths[1].elementId).toBe("stp-sc");
  });

  it("extracts decorative layers", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <g id="background">
          <rect width="100" height="100" fill="blue"/>
        </g>
        <g id="provinces">
          <path id="ber" d="M10,10 L30,10 L30,30 L10,30 Z"/>
        </g>
        <g id="borders">
          <path d="M0,0 L100,0"/>
        </g>
      </svg>
    `;

    const result = parseSvg(svg);
    expect(result.decorativeElements).toHaveLength(2);
    expect(result.decorativeElements.map(e => e.id)).toContain("background");
    expect(result.decorativeElements.map(e => e.id)).toContain("borders");
    expect(result.decorativeElements.map(e => e.id)).not.toContain("provinces");
  });

  it("extracts text styles", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <g id="provinces">
          <path id="ber" d="M10,10 L30,10 L30,30 L10,30 Z"/>
        </g>
        <g id="text">
          <text x="20" y="25" font-size="12" font-family="Arial" fill="#333">Berlin</text>
        </g>
      </svg>
    `;

    const result = parseSvg(svg);
    expect(result.textElements[0].styles).toEqual({
      fontSize: "12",
      fontFamily: "Arial",
      fill: "#333",
    });
  });

  it("extracts text rotation from transform attribute", () => {
    const svg = `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">
        <g id="provinces">
          <path id="ber" d="M10,10 L30,10 L30,30 L10,30 Z"/>
        </g>
        <g id="text">
          <text x="20" y="25" transform="rotate(45 20 25)">Berlin</text>
        </g>
      </svg>
    `;

    const result = parseSvg(svg);
    expect(result.textElements[0].rotation).toBe(45);
  });
});
