import { ICssParser } from "./css-parser";
import { IStyles } from "../../types";

/**
 * Parses a string of CSS styles into a dictionary of styles.
 */
interface IStyleParser {
    parse(styles: string): IStyles;
}

/**
 * Parses a string of CSS styles into a dictionary of styles.
 */
class StyleParser implements IStyleParser {
    private readonly cssParser: ICssParser;
    private readonly styleMap: Record<string, keyof IStyles> = {
        'fill': 'fill',
        'stroke': 'stroke',
        'stroke-width': 'strokeWidth',
        'stroke-dasharray': 'strokeDasharray',
        'stroke-dashoffset': 'strokeDashoffset',
        'stroke-opacity': 'strokeOpacity',
        'fill-opacity': 'fillOpacity',
        'stroke-miterlimit': 'strokeMiterlimit',
        'font-size': 'fontSize',
        'font-family': 'fontFamily',
        'font-weight': 'fontWeight',
        'font-style': 'fontStyle',
        'letter-spacing': 'letterSpacing',
        'transform': 'transform',
    };

    constructor(cssParser: ICssParser) {
        this.cssParser = cssParser;
    }

    public parse(styles: string): IStyles {
        const cssStyles = this.cssParser.parse(styles);
        const result: Partial<IStyles> = {};

        for (const [cssKey, styleKey] of Object.entries(this.styleMap)) {
            if (cssStyles[cssKey]) {
                result[styleKey] = cssStyles[cssKey];
            }
        }

        return result as IStyles;
    }
}

export { StyleParser, IStyleParser }