import service from "../store/service";

const ProvinceLongNames: Record<string, string> = {
    "Province1": "Province One",
    "Province2": "Province Two",
}

const variant: typeof service.endpoints.listVariants.Types.ResultType[0] = {
    Name: "Dummy Variant",
    Nations: ["Nation1", "Nation2"],
    PhaseTypes: ["Spring", "Fall"],
    Seasons: ["Spring", "Fall"],
    UnitTypes: ["Army", "Fleet"],
    SvgVersion: "1.0",
    ProvinceLongNames: {
        "Province1": "Province One",
        "Province2": "Province Two",
    },
    NationColors: {
        "Nation1": "#FF0000",
        "Nation2": "#0000FF",
    },
    CreatedBy: "Admin",
    Version: "1.0",
    Description: "This is a dummy variant for testing purposes.",
    Rules: "Standard rules apply.",
    OrderTypes: ["Move", "Hold", "Support", "Convoy"],
    Start: {
        Year: 1901,
        Season: "Spring",
        Type: "Standard",
        SCs: {
            "Province1": "Nation1",
            "Province2": "Nation2",
        },
        Units: {
            "Province1": { Type: "Army", Nation: "Nation1" },
            "Province2": { Type: "Fleet", Nation: "Nation2" },
        },
        Map: "dummy-map.svg",
    },
    Graph: {
        Nodes: {
            "Province1": {
                Name: "Province1",
                Subs: {},
                SC: "Nation1",
            },
            "Province2": {
                Name: "Province2",
                Subs: {},
                SC: "Nation2",
            },
        },
    },
    Links: [],
    ExtraDominanceRules: null,
    getUnitTypeSrc: (unitType: string) => `https://diplicity-engine.appspot.com/Variant/Classical/Units/${unitType}.svg`,
    getProvinceLongName: (province: string) => ProvinceLongNames[province] || province,
};

export { variant }
