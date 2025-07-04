interface IFilter {
    filter: (elements: Element[]) => Element[];
}

interface IFilterFactory {
    create(filterFn: (elements: Element[]) => Element[]): IFilter;
}

class Filter implements IFilter {
    constructor(private filterFn: (elements: Element[]) => Element[]) { }

    public filter(elements: Element[]): Element[] {
        return this.filterFn(elements);
    }
}

class FilterFactory implements IFilterFactory {
    public create(filterFn: (elements: Element[]) => Element[]): IFilter {
        return new Filter(filterFn);
    }
}

export { IFilter, IFilterFactory, FilterFactory }
