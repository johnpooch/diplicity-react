interface IValidator {
    validate(element: Element): boolean;
}

class ValidationError extends Error {
    constructor(message: string) {
        super(message);
        this.name = "ValidationError";
    }
}

abstract class Validator implements IValidator {
    public abstract validate(element: Element): boolean;
}

abstract class QuerySelectorValidator extends Validator {
    protected abstract querySelector: string;
    protected abstract elementName: string;

    public validate(element: Element): boolean {
        const foundElement = element.querySelector(this.querySelector);
        if (!foundElement) {
            throw new ValidationError(`Element ${this.elementName} not found`);
        }
        return true;
    }
}

class HasViewBoxValidator extends Validator {
    public validate(element: Element): boolean {
        const viewBox = element.getAttribute("viewBox");
        if (!viewBox) {
            throw new ValidationError("SVG element does not have a viewBox attribute");
        }
        return true;
    }
}
class HasBackgroundLayerValidator extends QuerySelectorValidator {
    protected querySelector = "#background";
    protected elementName = "background";
}

class HasForegroundLayerValidator extends QuerySelectorValidator {
    protected querySelector = "#foreground";
    protected elementName = "foreground";
}

class HasSupplyCentersLayerValidator extends QuerySelectorValidator {
    protected querySelector = "#supply-centers";
    protected elementName = "supply-centers";
}

class HasProvinceCentersLayerValidator extends QuerySelectorValidator {
    protected querySelector = "#province-centers";
    protected elementName = "province-centers";
}

class HasNamesLayerValidator extends QuerySelectorValidator {
    protected querySelector = "#names";
    protected elementName = "names";
}

class HasProvincesLayerValidator extends QuerySelectorValidator {
    protected querySelector = "#provinces";
    protected elementName = "provinces";
}

export { HasBackgroundLayerValidator, HasForegroundLayerValidator, HasSupplyCentersLayerValidator, HasProvinceCentersLayerValidator, HasNamesLayerValidator, HasProvincesLayerValidator, IValidator, HasViewBoxValidator };