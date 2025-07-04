import { IStyleParser } from "../util/style-parser";
import { ICenter, IPath, IText } from "../../types";
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
        const tspan = element.querySelector("tspan") as SVGTSpanElement;

        const fallbackTextPoint = {
            x: parseFloat(element.getAttribute("x") || "0"),
            y: parseFloat(element.getAttribute("y") || "0"),
        }
        const textPoint = {
            x: parseFloat(tspan.getAttribute("x") || "0"),
            y: parseFloat(tspan.getAttribute("y") || "0"),
        }

        const point = {
            x: textPoint.x || fallbackTextPoint.x,
            y: textPoint.y || fallbackTextPoint.y,
        }

        if (element.textContent === "Norwegian Sea") {
            console.log("Text element:", element);
            console.log("styles", element.getAttribute("style"));
        }

        const parsedStyles = this.styleParser.parse(element.getAttribute("style") || "");

        const transform = element.getAttribute("transform") || "";

        return {
            id: element.getAttribute("id") || "",
            value: element.textContent || "",
            styles: parsedStyles,
            transform: transform,
            point,
        };
    }
}

export { ISerializer, PathSerializer, CenterSerializer, TextSerializer }