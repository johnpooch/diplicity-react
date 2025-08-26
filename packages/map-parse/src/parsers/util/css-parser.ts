/**
 * Parses a string of CSS styles into a dictionary of styles.
 */
interface ICssParser {
    parse(css: string): Record<string, string>;
}

/**
 * Parses a string of CSS styles into a dictionary of styles.
 */
class CssParser implements ICssParser {
    parse(css: string): Record<string, string> {
        const regex = /([\w-]*)\s*:\s*([^;]*)/g;
        let match;
        const properties: Record<string, string> = {};
        while ((match = regex.exec(css))) {
            properties[match[1]] = match[2].trim();
        }
        return properties;
    }
}

export { ICssParser, CssParser }