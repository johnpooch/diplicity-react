import { IPoint } from "../../types";

/**
 * Determines the center of a path element.
 */
interface ICenterParser {
    parse(element: Element): IPoint;
}

/**
 * Determines the center of a path element.
 */
class CenterParser implements ICenterParser {
    public parse(element: Element): IPoint {
        const d = element.getAttribute("d") || "";
        const match = /^[Mm]\s+([\d.-]+(?:e[+-]?\d+)?),([\d.-]+(?:e[+-]?\d+)?)\s+/.exec(d);
        if (!match) throw new Error(`Invalid d attribute: ${d}`);
        return {
            x: Number(match[1]),
            y: Number(match[2]),
        };
    }
}

export { ICenterParser, CenterParser }