/**
 * Converts an element into another type of element, e.g. converting a polygon
 * into a path.
 */
interface IElementConverter {
    convert(element: Element): Element;
}

/**
 * Factory for creating element converters.
 */
interface IElementConverterFactory {
    create(element: Element): IElementConverter;
}


/**
 * Base class for converting elements into path elements.
 */
abstract class PathConverter implements IElementConverter {
    private readonly document: Document;

    constructor(document: Document) {
        this.document = document;
    }

    protected abstract buildPath(element: Element): string;
    protected abstract expectedTag: string;

    public convert(element: Element): SVGPathElement {
        if (element.tagName !== this.expectedTag) {
            throw new Error(`${this.constructor.name} expects a ${this.expectedTag}`);
        }
        const path = this.buildPath(element);
        const pathElement = this.document.createElementNS("http://www.w3.org/2000/svg", "path");
        pathElement.setAttribute("d", path);
        pathElement.setAttribute("style", element.getAttribute("style") || "");
        pathElement.setAttribute("id", element.getAttribute("id") || "");
        return pathElement;
    }
}

/**
 * Converts a rect element into a path element.
 */
class RectConverter extends PathConverter {
    protected expectedTag = "rect";

    protected buildPath(element: Element): string {
        const x = element.getAttribute("x") || "0";
        const y = element.getAttribute("y") || "0";
        const width = element.getAttribute("width") || "0";
        const height = element.getAttribute("height") || "0";
        return `M${x} ${y} L${x + width} ${y} L${x + width} ${y + height} L${x} ${y + height} Z`;
    }
}

/**
 * Converts a polygon element into a path element.
 */
class PolygonConverter extends PathConverter {
    protected expectedTag = "polygon";

    protected buildPath(element: Element): string {
        // const points = element.points;
        const points = element.getAttribute("points")?.split(" ") || [];
        let pathData = "";

        for (let i = 0; i < points.length; i++) {
            const point = points[i].split(",");
            if (i === 0) {
                pathData = `M ${point[0]} ${point[1]}`;
            } else {
                pathData += ` L ${point[0]} ${point[1]}`;
            }
        }
        pathData += " Z";
        return pathData;
    }
}

/**
 * Converts a polyline element into a path element.
 */
class PolylineConverter extends PathConverter {
    protected expectedTag = "polyline";

    protected buildPath(element: Element): string {
        const pointsAttr = element.getAttribute("points") || "";

        // Split by spaces to get all numbers, then group into coordinate pairs
        const numbers = pointsAttr.trim().split(/\s+/).map(num => parseFloat(num));

        const coordinatePairs = [];
        for (let i = 0; i < numbers.length; i += 2) {
            if (i + 1 < numbers.length) {
                coordinatePairs.push({ x: numbers[i], y: numbers[i + 1] });
            }
        }

        let pathData = "";
        for (let i = 0; i < coordinatePairs.length; i++) {
            const { x, y } = coordinatePairs[i];
            if (i === 0) {
                pathData = `M ${x} ${y}`;
            } else {
                pathData += ` L ${x} ${y}`;
            }
        }
        return pathData;
    }
}

class LineConverter extends PathConverter {
    protected expectedTag = "line";

    protected buildPath(element: Element): string {
        const x1 = element.getAttribute("x1") || "0";
        const y1 = element.getAttribute("y1") || "0";
        const x2 = element.getAttribute("x2") || "0";
        const y2 = element.getAttribute("y2") || "0";
        return `M ${x1} ${y1} L ${x2} ${y2}`;
    }
}

/**
 * Passes through the element without converting it.
 */
class PassThroughConverter implements IElementConverter {
    public convert(element: Element): Element {
        if (element.tagName !== "path") {
            throw new Error("PassThroughConverter expects an SVGPathElement");
        }
        return element;
    }
}

/**
 * Factory for creating element converters.
 */
class PathConverterFactory implements IElementConverterFactory {
    private readonly document: Document;

    constructor(document: Document) {
        this.document = document;
    }

    public create(element: Element): IElementConverter {
        if (element.tagName === "rect") {
            return new RectConverter(this.document);
        }
        if (element.tagName === "polygon") {
            return new PolygonConverter(this.document);
        }
        if (element.tagName === "polyline") {
            return new PolylineConverter(this.document);
        }
        if (element.tagName === "line") {
            return new LineConverter(this.document);
        }
        if (element.tagName === "path") {
            return new PassThroughConverter();
        }
        throw new Error(`Unsupported element tag: ${element.tagName}`);
    }
}

export { RectConverter, PolygonConverter, PolylineConverter, IElementConverterFactory, PathConverterFactory }