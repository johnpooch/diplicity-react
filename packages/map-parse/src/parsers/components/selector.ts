interface ISelector {
    select(element: Element): Element[];
}

interface ISelectorFactory {
    create(selector: string): ISelector;
}

class QuerySelector implements ISelector {
    constructor(private selector: string) { }

    public select(element: Element): Element[] {
        return Array.from(element.querySelectorAll(this.selector));
    }
}

class SelectorFactory implements ISelectorFactory {
    public create(selector: string): ISelector {
        return new QuerySelector(selector);
    }
}

export { ISelector, ISelectorFactory, SelectorFactory }
