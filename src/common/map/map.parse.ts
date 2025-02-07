import { Map, Point, Text, PathStyles } from "./map.parse.types";

const convertCssStringToObject = (css: string) => {
    const regex = /([\w-]*)\s*:\s*([^;]*)/g;
    let match;
    const properties: Record<string, string> = {};
    while ((match = regex.exec(css))) {
        properties[match[1]] = match[2].trim();
    }
    return properties;
};


const recognizedTags = ["path", "polygon", "polyline", "rect"];

class SvgParser {
    private svgString: string;

    constructor(svgString: string) {
        console.log("Initialized with string: ", svgString);
        this.svgString = svgString;
    }

    public parse(): Map {
        const parser = new DOMParser();
        const doc = parser.parseFromString(this.svgString, "image/svg+xml");
        const root = doc.documentElement;

        return {
            height: this.getHeight(root),
            width: this.getWidth(root),
            backgroundElements: this.parseBackgroundElements(root),
            borders: this.parseBorders(root),
            provinces: this.parseProvinces(root),
            impassableProvinces: this.parseImpassableProvinces(root)
        };
    }

    private getHeight(root: Element): number {
        console.log("Getting height for selector: #background-rect");
        const element = root.querySelector("#background-rect");
        console.log("Element: ", element);
        return parseFloat(element?.getAttribute("height") || "0");
    }

    private getWidth(root: Element): number {
        console.log("Getting width for selector: #background-rect");
        const element = root.querySelector("#background-rect");
        console.log("Element: ", element);
        return parseFloat(element?.getAttribute("width") || "0");
    }

    private convertRectToPath(rect: Element): Element {
        const x = parseFloat(rect.getAttribute("x") || "0");
        const y = parseFloat(rect.getAttribute("y") || "0");
        const width = parseFloat(rect.getAttribute("width") || "0");
        const height = parseFloat(rect.getAttribute("height") || "0");
        const path = `M${x} ${y} L${x + width} ${y} L${x + width} ${y + height} L${x} ${y + height} Z`;
        const pathElement = document.createElementNS("http://www.w3.org/2000/svg", "path");
        pathElement.setAttribute("d", path);
        pathElement.setAttribute("style", rect.getAttribute("style") || "");
        return pathElement;
    }

    private convertPolygonToPath(polygon: Element): Element {
        const points = polygon.getAttribute("points") || "";
        const pointsArray = points.trim().split(" ");
        let pathData = `M ${pointsArray[0]}`;
        for (let i = 1; i < pointsArray.length; i++) {
            pathData += ` L ${pointsArray[i]}`;
        }
        pathData += " Z";
        const pathElement = document.createElementNS("http://www.w3.org/2000/svg", "path");
        pathElement.setAttribute("d", pathData);
        pathElement.setAttribute("style", polygon.getAttribute("style") || "");
        return pathElement;
    }

    private convertPolylineToPath(polyline: Element): Element {
        const points = polyline.getAttribute("points") || "";
        const path = `M${points}`;
        const pathElement = document.createElementNS("http://www.w3.org/2000/svg", "path");
        pathElement.setAttribute("d", path);
        pathElement.setAttribute("style", polyline.getAttribute("style") || "");
        return pathElement;
    }

    private parseBackgroundElements(root: Element): Map["backgroundElements"] {
        console.log("Parsing background elements");
        const backgroundLayer = root.querySelector("#background");
        const elements = backgroundLayer?.querySelectorAll("path, rect");
        console.log("Elements: ", elements);
        if (!elements) return [];
        return Array.from(elements).map(element => {
            if (element.tagName === "rect") {
                const path = this.convertRectToPath(element);
                return {
                    path: path.getAttribute("d") || "",
                    styles: this.parsePathStyles(path)
                }
            }
            return {
                path: element.getAttribute("d") || "",
                styles: this.parsePathStyles(element)
            }
        })
    }

    private parseBorders(root: Element): Map["borders"] {
        const foregroundLayer = root.querySelector("#foreground");
        const elements = foregroundLayer?.querySelectorAll("path, polygon, polyline");
        if (!elements) return [];

        // Only include elements that don't have fill:url(#impassableStripes)
        const filteredElements = Array.from(elements).filter(element => {
            const fill = convertCssStringToObject(element.getAttribute("style") || "").fill;
            return fill !== "url(#impassableStripes)";
        })

        // If element is polyline, return points and transform
        return Array.from(filteredElements).map(element => {
            if (element.tagName === "polygon" || element.tagName === "polyline") {
                const path = element.tagName === "polygon" ? this.convertPolygonToPath(element) : this.convertPolylineToPath(element);
                return {
                    path: path.getAttribute("d") || "",
                }
            }
            return {
                path: element.getAttribute("d") || ""
            }
        })
    }

    private parseImpassableProvinces(root: Element): Map["impassableProvinces"] {
        const foregroundLayer = root.querySelector("#foreground");
        const elements = foregroundLayer?.querySelectorAll("path, polygon, polyline");
        if (!elements) return [];

        // Only include elements that don't have fill:url(#impassableStripes)
        const filteredElements = Array.from(elements).filter(element => {
            const fill = convertCssStringToObject(element.getAttribute("style") || "").fill;
            return fill === "url(#impassableStripes)";
        })

        // If element is polyline, return points and transform
        return Array.from(filteredElements).map(element => {
            if (element.tagName === "polygon" || element.tagName === "polyline") {
                const path = element.tagName === "polygon" ? this.convertPolygonToPath(element) : this.convertPolylineToPath(element);
                return {
                    path: path.getAttribute("d") || "",
                }
            }
            return {
                path: element.getAttribute("d") || ""
            }
        })
    }

    private parseProvinces(root: Element): Map["provinces"] {
        console.log("Parsing provinces elements");
        const provincesLayer = root.querySelector("#provinces");
        const supplyCentersLayer = root.querySelector("#supply-centers");
        const provinceCentersLayer = root.querySelector("#province-centers");
        const namesLayer = root.querySelector("#names");
        const elements = provincesLayer?.querySelectorAll(recognizedTags.join(", "));
        if (!elements) return [];
        return Array.from(elements).map(element => {
            const escapedId = element.id.replace("/", "\\/");
            const supplyCenter = supplyCentersLayer?.querySelector(`#${escapedId}Center`);
            const provinceCenter = provinceCentersLayer?.querySelector(`#${escapedId}Center`);
            const [x, y] = supplyCenter ? this.parseDCenter(supplyCenter as HTMLElement) : provinceCenter ? this.parseDCenter(provinceCenter as HTMLElement) : [0, 0];

            if (element.tagName === "polygon") {
                const path = this.convertPolygonToPath(element);
                return {
                    id: element.id,
                    center: { x, y },
                    supplyCenter: Boolean(supplyCenter),
                    path: path.getAttribute("d") || "",
                    text: this.parseText(namesLayer?.querySelector(`#${escapedId}`) || null),
                }
            } else {

                return {
                    id: element.id,
                    center: { x, y },
                    supplyCenter: !!supplyCenter,
                    path: element.getAttribute("d") || "",
                    text: this.parseText(namesLayer?.querySelector(`#${escapedId}`) || null),
                }
            }
        });
    }

    private parseDCenter(element: HTMLElement): [number, number] {
        const d = element.getAttribute("d") || "";
        const match = /^m\s+([\d-.]+),([\d-.]+)\s+/.exec(d);
        if (!match) throw new Error(`Invalid d attribute: ${d}`);
        return [Number(match[1]), Number(match[2])];
    }

    private parsePoint(element: Element): Point {
        return {
            x: parseFloat(element.getAttribute("x") || "0"),
            y: parseFloat(element.getAttribute("y") || "0")
        };
    }

    private parseText(element: Element | null): Text | undefined {
        if (!element) return undefined
        const tspan = element.querySelector("tspan");
        if (!tspan) return undefined;
        const cssStyles = convertCssStringToObject(element.getAttribute("style") || "")
        const textPoint = this.parsePoint(tspan);
        const textOffset = this.parsePoint(element);
        const x = textPoint.x - textOffset.x;
        const y = textPoint.y - textOffset.y;
        return {
            value: element.textContent || "",
            styles: {
                fontSize: cssStyles["font-size"] || "",
                fontFamily: cssStyles["font-family"] || "",
                fontWeight: cssStyles["font-weight"] || "",
                transform: cssStyles.transform || ""
            },
            point: { x, y }
        };
    }

    private parsePathStyles(element: Element): PathStyles {
        const cssStyles = convertCssStringToObject(element.getAttribute("style") || "")
        return {
            fill: cssStyles.fill || "",
            stroke: cssStyles.stroke,
            strokeDasharray: cssStyles["stroke-dasharray"],
            strokeMiterlimit: cssStyles["stroke-miterlimit"],
            strokeOpacity: cssStyles["stroke-opacity"],
            strokeWidth: cssStyles["stroke-width"],
        }
    }
}

const parseSvg = (svgString: string): Map => {
    return new SvgParser(svgString).parse();
};

export { parseSvg };