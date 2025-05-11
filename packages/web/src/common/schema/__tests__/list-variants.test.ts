import { test, expect } from "vitest";
import { listVariantsSchema } from "../list-variants";

const rawData = {
    "Name": "variants",
    "Properties": [
        {
            "Name": "Classical",
            "Properties": {
                "Name": "Classical",
                "Nations": [
                    "Austria",
                    "England",
                    "France",
                    "Germany",
                    "Italy",
                    "Turkey",
                    "Russia"
                ],
                "PhaseTypes": [
                    "Movement",
                    "Retreat",
                    "Adjustment"
                ],
                "Seasons": [
                    "Spring",
                    "Fall"
                ],
                "UnitTypes": [
                    "Army",
                    "Fleet"
                ],
                "SVGVersion": "9",
                "ProvinceLongNames": {
                    "adr": "Adriatic Sea",
                    "aeg": "Aegean Sea",
                    "alb": "Albania",
                    "ank": "Ankara",
                    "apu": "Apulia",
                    "arm": "Armenia",
                    "bal": "Baltic Sea",
                    "bar": "Barents Sea",
                    "bel": "Belgium",
                    "ber": "Berlin",
                    "bla": "Black Sea",
                    "boh": "Bohemia",
                    "bot": "Gulf of Bothnia",
                    "bre": "Brest",
                    "bud": "Budapest",
                    "bul": "Bulgaria",
                    "bul/ec": "Bulgaria (EC)",
                    "bul/sc": "Bulgaria (SC)",
                    "bur": "Burgundy",
                    "cly": "Clyde",
                    "con": "Constantinople",
                    "den": "Denmark",
                    "eas": "East Med",
                    "edi": "Edinburgh",
                    "eng": "English Channel",
                    "fin": "Finland",
                    "gal": "Galicia",
                    "gas": "Gascony",
                    "gol": "Gulf of Lyon",
                    "gre": "Greece",
                    "hel": "Heligoland Bight",
                    "hol": "Holland",
                    "ion": "Ionian Sea",
                    "iri": "Irish Sea",
                    "kie": "Kiel",
                    "lon": "London",
                    "lvn": "Livonia",
                    "lvp": "Liverpool",
                    "mar": "Marseilles",
                    "mid": "Mid-Atlantic",
                    "mos": "Moscow",
                    "mun": "Munich",
                    "naf": "North Africa",
                    "nap": "Naples",
                    "nat": "North Atlantic",
                    "nrg": "Norwegian Sea",
                    "nth": "North Sea",
                    "nwy": "Norway",
                    "par": "Paris",
                    "pic": "Picardy",
                    "pie": "Piedmont",
                    "por": "Portugal",
                    "pru": "Prussia",
                    "rom": "Rome",
                    "ruh": "Ruhr",
                    "rum": "Rumania",
                    "ser": "Serbia",
                    "sev": "Sevastopol",
                    "sil": "Silesia",
                    "ska": "Skagerakk (SKA)",
                    "smy": "Smyrna",
                    "spa": "Spain",
                    "spa/nc": "Spain (NC)",
                    "spa/sc": "Spain (SC)",
                    "stp": "St. Petersburg",
                    "stp/nc": "St. Petersburg (NC)",
                    "stp/sc": "St. Petersburg (SC)",
                    "swe": "Sweden",
                    "syr": "Syria",
                    "tri": "Trieste",
                    "tun": "Tunis",
                    "tus": "Tuscany",
                    "tyr": "Tyrolia",
                    "tys": "Tyrrhenian Sea",
                    "ukr": "Ukraine",
                    "ven": "Venice",
                    "vie": "Vienna",
                    "wal": "Wales",
                    "war": "Warsaw",
                    "wes": "West Mediterranean",
                    "yor": "Yorkshire"
                },
                "NationColors": null,
                "CreatedBy": "Allan B. Calhamer",
                "Version": "",
                "Description": "The original Diplomacy.",
                "Rules": "The first to 18 Supply Centers (SC) is the winner. \nKiel and Constantinople have a canal, so fleets can exit on either side. \nArmies can move from Denmark to Kiel.",
                "Start": {
                    "Year": 1901,
                    "Season": "Spring",
                    "Type": "Movement",
                    "SCs": {
                        "ank": "Turkey",
                        "ber": "Germany",
                        "bre": "France",
                        "bud": "Austria",
                        "con": "Turkey",
                        "edi": "England",
                        "kie": "Germany",
                        "lon": "England",
                        "lvp": "England",
                        "mar": "France",
                        "mos": "Russia",
                        "mun": "Germany",
                        "nap": "Italy",
                        "par": "France",
                        "rom": "Italy",
                        "sev": "Russia",
                        "smy": "Turkey",
                        "stp": "Russia",
                        "tri": "Austria",
                        "ven": "Italy",
                        "vie": "Austria",
                        "war": "Russia"
                    },
                    "Units": {
                        "ank": {
                            "Type": "Fleet",
                            "Nation": "Turkey"
                        },
                        "ber": {
                            "Type": "Army",
                            "Nation": "Germany"
                        },
                        "bre": {
                            "Type": "Fleet",
                            "Nation": "France"
                        },
                        "bud": {
                            "Type": "Army",
                            "Nation": "Austria"
                        },
                        "con": {
                            "Type": "Army",
                            "Nation": "Turkey"
                        },
                        "edi": {
                            "Type": "Fleet",
                            "Nation": "England"
                        },
                        "kie": {
                            "Type": "Fleet",
                            "Nation": "Germany"
                        },
                        "lon": {
                            "Type": "Fleet",
                            "Nation": "England"
                        },
                        "lvp": {
                            "Type": "Army",
                            "Nation": "England"
                        },
                        "mar": {
                            "Type": "Army",
                            "Nation": "France"
                        },
                        "mos": {
                            "Type": "Army",
                            "Nation": "Russia"
                        },
                        "mun": {
                            "Type": "Army",
                            "Nation": "Germany"
                        },
                        "nap": {
                            "Type": "Fleet",
                            "Nation": "Italy"
                        },
                        "par": {
                            "Type": "Army",
                            "Nation": "France"
                        },
                        "rom": {
                            "Type": "Army",
                            "Nation": "Italy"
                        },
                        "sev": {
                            "Type": "Fleet",
                            "Nation": "Russia"
                        },
                        "smy": {
                            "Type": "Army",
                            "Nation": "Turkey"
                        },
                        "stp/sc": {
                            "Type": "Fleet",
                            "Nation": "Russia"
                        },
                        "tri": {
                            "Type": "Fleet",
                            "Nation": "Austria"
                        },
                        "ven": {
                            "Type": "Army",
                            "Nation": "Italy"
                        },
                        "vie": {
                            "Type": "Army",
                            "Nation": "Austria"
                        },
                        "war": {
                            "Type": "Army",
                            "Nation": "Russia"
                        }
                    },
                    "Map": ""
                },
            },
            "Type": "Variant",
            "Links": [
                {
                    "Rel": "map",
                    "URL": "https://diplicity-engine.appspot.com/Variant/Classical/Map.svg",
                    "Method": "GET"
                },
                {
                    "Rel": "unit-Army",
                    "URL": "https://diplicity-engine.appspot.com/Variant/Classical/Units/Army.svg",
                    "Method": "GET"
                },
                {
                    "Rel": "unit-Fleet",
                    "URL": "https://diplicity-engine.appspot.com/Variant/Classical/Units/Fleet.svg",
                    "Method": "GET"
                },
                {
                    "Rel": "flag-England",
                    "URL": "https://diplicity-engine.appspot.com/Variant/Classical/Flags/England.svg",
                    "Method": "GET"
                },
                {
                    "Rel": "flag-France",
                    "URL": "https://diplicity-engine.appspot.com/Variant/Classical/Flags/France.svg",
                    "Method": "GET"
                },
                {
                    "Rel": "flag-Germany",
                    "URL": "https://diplicity-engine.appspot.com/Variant/Classical/Flags/Germany.svg",
                    "Method": "GET"
                },
                {
                    "Rel": "flag-Italy",
                    "URL": "https://diplicity-engine.appspot.com/Variant/Classical/Flags/Italy.svg",
                    "Method": "GET"
                },
                {
                    "Rel": "flag-Russia",
                    "URL": "https://diplicity-engine.appspot.com/Variant/Classical/Flags/Russia.svg",
                    "Method": "GET"
                },
                {
                    "Rel": "flag-Turkey",
                    "URL": "https://diplicity-engine.appspot.com/Variant/Classical/Flags/Turkey.svg",
                    "Method": "GET"
                },
                {
                    "Rel": "flag-Austria",
                    "URL": "https://diplicity-engine.appspot.com/Variant/Classical/Flags/Austria.svg",
                    "Method": "GET"
                }
            ]
        },
    ],
}

const parsed = listVariantsSchema.parse(rawData);

const variant = parsed.Properties[0].Properties;

test("Basic parsing works as expected", () => {
    expect(variant.Name).toBe("Classical");
})

test("Getting long province names works as expected", () => {
    expect(variant.Provinces["eng"]).toBe("English Channel");
})

test("Getting nation colors works as expected", () => {
    expect(variant.Colors).toEqual({});
});

test("Getting flag links works as expected", () => {
    expect(variant.Flags["England"]).toBe("https://diplicity-engine.appspot.com/Variant/Classical/Flags/England.svg");
})

test("Getting unit links works as expected", () => {
    expect(variant.Units["Army"]).toBe("https://diplicity-engine.appspot.com/Variant/Classical/Units/Army.svg");
})

test("Getting map link works as expected", () => {
    expect(variant.Map).toBe("https://diplicity-engine.appspot.com/Variant/Classical/Map.svg");
})