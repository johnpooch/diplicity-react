import { describe, expect, test } from "vitest";
import CLASSICAL_DSVG from "./classicalMap.dsvg?raw";
import { DiplicityMap } from "./mapRenderer";
import { sanitizeSvg, sanitizeSvgElement } from "./sanitizeSvg";

const SVG_OPEN =
  '<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">';

const wrap = (markup: string) => `${SVG_OPEN}${markup}</svg>`;

const isGeneratedPrefix = (name: string) => /^(xmlns:)?ns\d+(:|$)/.test(name);

const describeTree = (markup: string): string[] => {
  const container = document.createElement("div");
  container.innerHTML = markup;
  return Array.from(container.querySelectorAll("*")).map((element) => {
    const attributes = Array.from(element.attributes)
      .filter((attribute) => !isGeneratedPrefix(attribute.name))
      .map((attribute) => `${attribute.name}=${attribute.value.trim()}`)
      .sort();
    const text =
      element.children.length === 0 ? (element.textContent ?? "").trim() : "";
    return `${element.tagName}[${attributes.join(" ")}]${text}`;
  });
};

describe("sanitizeSvg", () => {
  test.each([
    ['<a xlink:href="java&#x09;script:alert(1)"><rect/></a>'],
    ['<a href="javascript:alert(1)"><rect/></a>'],
    ['<animate attributeName="href" values="javascript:alert(1)"/>'],
    ['<set attributeName="href" from="javascript:alert(1)"/>'],
    ['<image href="javascript:alert(1)"/>'],
    ['<image href="data:image/svg+xml;base64,PHN2Zy8+"/>'],
    ['<use href="data:image/svg+xml;base64,PHN2Zy8+#a"/>'],
  ])("removes script URLs from %s", (markup) => {
    const clean = sanitizeSvg(wrap(markup));

    expect(clean).not.toMatch(/javascript|data:image\/svg/i);
    expect(clean).not.toMatch(/<animate|<set/i);
  });

  test("removes event handlers, scripts and foreign objects", () => {
    const clean = sanitizeSvg(
      wrap(
        '<rect id="r" onclick="alert(1)"/><script>alert(2)</script><foreignObject><div>x</div></foreignObject>'
      )
    );

    expect(clean).not.toMatch(/onclick|<script|alert|foreignObject/i);
    expect(clean).toContain('id="r"');
  });

  test("keeps same-document references and raster data images", () => {
    const clean = sanitizeSvg(
      wrap(
        '<use xlink:href="#tile"/><use href="https://example.com/x.svg#a"/><image xlink:href="data:image/png;base64,iVBORw0KGgo="/><path d="M0 0" fill="url(#g)"/>'
      )
    );

    expect(clean).toContain('xlink:href="#tile"');
    expect(clean).not.toContain("example.com");
    expect(clean).toContain('xlink:href="data:image/png;base64,iVBORw0KGgo="');
    expect(clean).toContain('fill="url(#g)"');
  });

  test("empties stylesheets that load external resources", () => {
    const clean = sanitizeSvg(
      wrap(
        "<style>@import url(https://example.com/x.css);</style><style>rect{fill:url(https://example.com/a)}</style><style>@font-face{font-family:'F';src:url(data:font/woff2;base64,AAAA)}</style>"
      )
    );

    expect(clean).not.toContain("example.com");
    expect(clean).toContain(
      "@font-face{font-family:'F';src:url(data:font/woff2;base64,AAAA)}"
    );
  });

  test("leaves the rendered classical board unchanged", () => {
    const board = new DiplicityMap(CLASSICAL_DSVG).render({
      nationColors: { England: "#2196F3", France: "#80DEEA" },
      supplyCenters: [{ province: "lon", nation: "England" }],
      units: [
        { province: "lon", nation: "England", type: "Fleet" },
        { province: "par", nation: "France", type: "Army" },
      ],
      orders: [
        { type: "Move", nation: "England", source: "lon", target: "eng" },
        { type: "Hold", nation: "France", source: "par" },
      ],
    });

    expect(describeTree(sanitizeSvg(board))).toEqual(describeTree(board));
  });
});

describe("sanitizeSvgElement", () => {
  test("returns the sanitised root svg element", () => {
    const element = sanitizeSvgElement(
      wrap('<rect id="r" onclick="alert(1)"/>')
    );

    expect(element.tagName).toBe("svg");
    expect(element.querySelector("#r")?.hasAttribute("onclick")).toBe(false);
  });
});
