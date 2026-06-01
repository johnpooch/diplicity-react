import { IElementConverterFactory } from "./converter";
import { parseMatrix, applyMatrixToPath } from "../util/path-transform";

/**
 * Normalizes an element by applying a transformation to it.
 */
interface INormalizer {
    normalize(element: Element): Element;
}

/**
 * Normalizes any element by converting it to a path element.
 */
class PathConverterNormalizer implements INormalizer {
    private readonly pathConverterFactory: IElementConverterFactory;

    constructor(pathConverterFactory: IElementConverterFactory) {
        this.pathConverterFactory = pathConverterFactory;
    }

    public normalize(element: Element): Element {
        return this.pathConverterFactory.create(element).convert(element);
    }
}

/**
 * Normalizes an element by applying a transformation to its id.
 */
class IdNormalizer implements INormalizer {
    private readonly normalizeFn: (id: string) => string;

    constructor(normalizeFn: (id: string) => string) {
        this.normalizeFn = normalizeFn;
    }

    public normalize(element: Element): Element {
        const id = element.getAttribute("id");
        if (id) {
            element.setAttribute("id", this.normalizeFn(id));
        }
        return element;
    }
}

/**
 * Bakes element-level transform attributes into path coordinates and removes the attribute.
 */
class TransformNormalizer implements INormalizer {
    public normalize(element: Element): Element {
        const transform = element.getAttribute("transform");
        if (!transform) return element;
        const matrix = parseMatrix(transform);
        if (!matrix) return element;
        const d = element.getAttribute("d");
        if (!d) return element;
        element.setAttribute("d", applyMatrixToPath(d, matrix));
        element.removeAttribute("transform");
        return element;
    }
}

export { INormalizer, PathConverterNormalizer, IdNormalizer, TransformNormalizer }