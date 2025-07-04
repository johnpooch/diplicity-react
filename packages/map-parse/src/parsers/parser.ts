import { IFilter } from "./components/filter";
import { INormalizer } from "./components/normalizer";
import { ISelector } from "./components/selector";
import { ISerializer } from "./components/serializer";

interface IParser<TNormalizedType extends Element, TOutput> {
    parse(element: Element): TOutput[];
}

class Parser<TNormalizedType extends Element, TOutput> implements IParser<TNormalizedType, TOutput> {
    private readonly selector: ISelector;
    private readonly filters: IFilter[];
    private readonly normalizers: INormalizer[];
    private readonly serializer: ISerializer<TNormalizedType, TOutput>;

    constructor(
        selector: ISelector,
        filters: IFilter[],
        normalizers: INormalizer[],
        serializer: ISerializer<TNormalizedType, TOutput>
    ) {
        this.selector = selector;
        this.filters = filters;
        this.normalizers = normalizers;
        this.serializer = serializer;
    }

    public parse(element: Element): TOutput[] {
        const selectedElements = this.selector.select(element);
        const filteredElements = this.filters.reduce((elements, filter) => filter.filter(elements), selectedElements);
        const normalizedElements = filteredElements.map(element =>
            this.normalizers.reduce((normalizedElement, normalizer) => normalizer.normalize(normalizedElement), element)
        );
        return normalizedElements.map(element => this.serializer.serialize(element as TNormalizedType));
    }
}

export { IParser, Parser }