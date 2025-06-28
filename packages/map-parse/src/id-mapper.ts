interface IIdMapper {
    getMappedId(id: string): string;
}

class IdMapper implements IIdMapper {
    private readonly idMap: Record<string, string>;

    constructor(idMap: Record<string, string>) {
        this.idMap = idMap;
    }

    public getMappedId(id: string): string {
        return this.idMap[id] || id;
    }
}

class IdMapperFactory {
    public create(idMap: Record<string, string>): IIdMapper {
        return new IdMapper(idMap);
    }
}

export { IdMapper, IIdMapper, IdMapperFactory }