import { IStyleParser } from "../util/style-parser";
import { ICenter, IPath, IText, ITspan } from "../../types";
import { ICenterParser } from "../util/center-parser";

/**
 * Serializes and element into an object.
 */
interface ISerializer<TElement extends Element, TOutput> {
    serialize(element: TElement): TOutput;
}

/**
 * Base class for validated serializers.
 */
abstract class ValidatedSerializer<TElement extends Element, TOutput> implements ISerializer<TElement, TOutput> {
    protected abstract validateElement(element: Element): TElement;
    protected abstract serializeElement(element: TElement): TOutput;

    public serialize(element: Element): TOutput {
        const validatedElement = this.validateElement(element);
        return this.serializeElement(validatedElement);
    }
}

/**
 * Base class for serializers that validate against an element type.
 */
abstract class TypeValidatedSerializer<TElement extends Element, TOutput> extends ValidatedSerializer<TElement, TOutput> {
    protected abstract expectedTag: string;
    protected validateElement(element: Element): TElement {
        if (element.tagName !== this.expectedTag) {
            throw new Error(`Invalid element: ${element}`);
        }
        return element as TElement;
    }
}

/**
 * Serializes a path element into an IPath object.
 */
class PathSerializer extends TypeValidatedSerializer<SVGPathElement, IPath> {
    protected expectedTag = "path";
    private readonly styleParser: IStyleParser;

    constructor(styleParser: IStyleParser) {
        super();
        this.styleParser = styleParser;
    }

    protected serializeElement(element: SVGPathElement): IPath {
        const styles = this.styleParser.parse(element.getAttribute("style") || "");
        return {
            id: element.getAttribute("id") || "",
            d: element.getAttribute("d") || "",
            styles,
        };
    }
}

/**
 * Serializes a path element into an ICenter object.
 */
class CenterSerializer extends TypeValidatedSerializer<SVGPathElement, ICenter> {
    protected expectedTag = "path";
    private readonly centerParser: ICenterParser;

    constructor(centerParser: ICenterParser) {
        super();
        this.centerParser = centerParser;
    }

    protected serializeElement(element: SVGPathElement): ICenter {
        return {
            id: element.getAttribute("id") || "",
            center: this.centerParser.parse(element),
        };
    }
}

/**
 * Serializes a text element into an IText object.
 */
class TextSerializer extends TypeValidatedSerializer<SVGTextElement, IText> {
    protected expectedTag = "text";
    private readonly styleParser: IStyleParser;

    constructor(styleParser: IStyleParser) {
        super();
        this.styleParser = styleParser;
    }

    protected validateElement(element: Element): SVGTextElement {
        const validatedElement = super.validateElement(element);
        if (validatedElement.querySelector("tspan") === null) {
            throw new Error(`Tspan not found for text element: ${validatedElement}`);
        }
        return validatedElement;
    }

    protected serializeElement(element: SVGTextElement): IText {
        const tspanElements = Array.from(element.querySelectorAll("tspan")) as SVGTSpanElement[];

        const tspans: ITspan[] = tspanElements.map(ts => ({
            value: ts.textContent || "",
            x: parseFloat(ts.getAttribute("x") || "0"),
            y: parseFloat(ts.getAttribute("y") || "0"),
        }));

        const fallbackTextPoint = {
            x: parseFloat(element.getAttribute("x") || "0"),
            y: parseFloat(element.getAttribute("y") || "0"),
        };

        const point = tspans.length > 0
            ? { x: tspans[0].x || fallbackTextPoint.x, y: tspans[0].y || fallbackTextPoint.y }
            : fallbackTextPoint;

        const value = tspans.map(ts => ts.value).join(" ");

        const parsedStyles = this.styleParser.parse(element.getAttribute("style") || "");

        // The font-size attribute holds the intended visual size. When Inkscape decomposes
        // a matrix transform it writes a computed (incorrect) value into the style, so the
        // attribute must take precedence.
        const fontSizeAttr = element.getAttribute("font-size");
        if (fontSizeAttr) {
            parsedStyles.fontSize = `${fontSizeAttr}px`;
        }

        // Tspan inline styles override text-element styles in SVG cascade. Merge all first-tspan
        // style properties into parsedStyles so font-family, font-size, etc. reflect the actual
        // rendered appearance (e.g. Inkscape sub-province labels where the text element carries
        // placeholder styles but the tspan holds the real font specification).
        const firstTspan = tspanElements[0];
        if (firstTspan) {
            const tspanParsed = this.styleParser.parse(firstTspan.getAttribute("style") || "");
            Object.assign(parsedStyles, Object.fromEntries(
                Object.entries(tspanParsed).filter(([, v]) => v !== undefined)
            ));
        }

        const transform = element.getAttribute("transform") || "";

        return {
            id: element.getAttribute("id") || "",
            value,
            tspans,
            styles: parsedStyles,
            transform,
            point,
        };
    }
}

export { ISerializer, PathSerializer, CenterSerializer, TextSerializer }