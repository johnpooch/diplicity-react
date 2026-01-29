import { describe, it, expect } from "vitest";
import { validateSvg } from "../svg";

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
