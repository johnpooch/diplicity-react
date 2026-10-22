import DOMPurify from "dompurify";

const HREF_ATTRIBUTES = new Set(["href", "xlink:href"]);
const RASTER_DATA_URI = /^data:image\/(png|jpeg|gif|webp);base64,/i;
const UNSAFE_STYLESHEET = /@import|expression\s*\(|javascript:|url\s*\(\s*['"]?(?!data:|#)/i;

const purifier = DOMPurify(window);

purifier.addHook("uponSanitizeAttribute", (node, data) => {
  if (!HREF_ATTRIBUTES.has(data.attrName)) return;
  const value = data.attrValue.trim();
  const allowed =
    value.startsWith("#") ||
    (node.nodeName.toLowerCase() === "image" && RASTER_DATA_URI.test(value));
  if (!allowed) {
    data.keepAttr = false;
  }
});

purifier.addHook("uponSanitizeElement", (node, data) => {
  if (data.tagName === "style" && UNSAFE_STYLESHEET.test(node.textContent ?? "")) {
    node.textContent = "";
  }
});

const config = {
  USE_PROFILES: { svg: true, svgFilters: true },
  ADD_TAGS: ["use"],
};

export const sanitizeSvg = (markup: string): string =>
  purifier.sanitize(markup, config);

export const sanitizeSvgElement = (markup: string): SVGSVGElement => {
  const fragment = purifier.sanitize(markup, {
    ...config,
    RETURN_DOM_FRAGMENT: true,
  });
  const element = fragment.firstElementChild;
  if (!(element instanceof SVGSVGElement)) {
    throw new Error("Sanitised markup is not an <svg> element");
  }
  return element;
};
