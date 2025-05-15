import { describe, test } from "vitest";
import { getOptions, transformResolution } from "../util";
import { getOrderSummary } from "../util";
import { getStepLabel } from "../util";
import { Phase, Variant } from "../store";

describe("transformResolution", () => {
    test("OK", () => {
        const resolution = "OK";
        const result = transformResolution(resolution);
        expect(result).toEqual({
            outcome: "Succeeded",
        });
    })
    test("ErrBounce:pie", () => {
        const resolution = "ErrBounce:pie";
        const result = transformResolution(resolution);
        expect(result).toEqual({
            outcome: "Bounced",
            by: "pie",
        });
    })
    test("ErrBounce:bul/ec", () => {
        const resolution = "ErrBounce:bul/ec";
        const result = transformResolution(resolution);
        expect(result).toEqual({
            outcome: "Bounced",
            by: "bul/ec",
        });
    })
    test("ErrSupportBroken:pie", () => {
        const resolution = "ErrSupportBroken:pie";
        const result = transformResolution(resolution);
        expect(result).toEqual({
            outcome: "Support broken",
            by: "pie",
        });
    })
    test("ErrInvalidSupporteeOrder", () => {
        const resolution = "ErrInvalidSupporteeOrder";
        const result = transformResolution(resolution);
        expect(result).toEqual({
            outcome: "Invalid order",
        });
    })
});

describe("getOrderSummary", () => {
    const mockVariant = {
        provinces: [
            { id: "lon", name: "London" },
            { id: "nth", name: "North Sea" },
            { id: "eng", name: "English Channel" },
            { id: "wal", name: "Wales" }
        ]
    } as unknown as Variant;

    const mockPhase = {
        units: [
            { province: { id: "lon" }, type: "army" },
            { province: { id: "nth" }, type: "fleet" },
            { province: { id: "eng" }, type: "fleet" },
            { province: { id: "wal" }, type: "army" }
        ]
    } as unknown as Phase;

    test("empty order shows nothing", () => {
        const order = {};
        const result = getOrderSummary(order, mockVariant, mockPhase);
        expect(result).toBe("");
    });

    test("partial order with only source", () => {
        const order = { source: "lon" };
        const result = getOrderSummary(order, mockVariant, mockPhase);
        expect(result).toBe("Army London...");
    });

    test("hold order", () => {
        const order = { source: "lon", type: "Hold" };
        const result = getOrderSummary(order, mockVariant, mockPhase);
        expect(result).toBe("Army London Hold");
    });

    test("partial move order", () => {
        const order = { source: "lon", type: "Move" };
        const result = getOrderSummary(order, mockVariant, mockPhase);
        expect(result).toBe("Army London Move to...");
    });

    test("complete move order", () => {
        const order = { source: "lon", type: "Move", target: "wal" };
        const result = getOrderSummary(order, mockVariant, mockPhase);
        expect(result).toBe("Army London Move to Wales");
    });

    test("partial support order - only source", () => {
        const order = { source: "lon", type: "Support" };
        const result = getOrderSummary(order, mockVariant, mockPhase);
        expect(result).toBe("Army London Support...");
    });

    test("partial support order - with aux", () => {
        const order = { source: "lon", type: "Support", aux: "wal" };
        const result = getOrderSummary(order, mockVariant, mockPhase);
        expect(result).toBe("Army London Support Wales to...");
    });

    test("complete support order", () => {
        const order = { source: "lon", type: "Support", aux: "wal", target: "nth" };
        const result = getOrderSummary(order, mockVariant, mockPhase);
        expect(result).toBe("Army London Support Wales to North Sea");
    });

    test("partial convoy order - only source", () => {
        const order = { source: "nth", type: "Convoy" };
        const result = getOrderSummary(order, mockVariant, mockPhase);
        expect(result).toBe("Fleet North Sea Convoy...");
    });

    test("partial convoy order - with aux", () => {
        const order = { source: "nth", type: "Convoy", aux: "lon" };
        const result = getOrderSummary(order, mockVariant, mockPhase);
        expect(result).toBe("Fleet North Sea Convoy London to...");
    });

    test("complete convoy order", () => {
        const order = { source: "nth", type: "Convoy", aux: "lon", target: "wal" };
        const result = getOrderSummary(order, mockVariant, mockPhase);
        expect(result).toBe("Fleet North Sea Convoy London to Wales");
    });
});

describe("getStepLabel", () => {
    test("source step", () => {
        const result = getStepLabel("source", {});
        expect(result).toBe("Select unit to order");
    });

    test("type step", () => {
        const result = getStepLabel("type", {});
        expect(result).toBe("Select order type");
    });

    test("target step", () => {
        const result = getStepLabel("target", {});
        expect(result).toBe("Select destination");
    });

    test("aux step with Support order", () => {
        const order = { type: "Support" };
        const result = getStepLabel("aux", order);
        expect(result).toBe("Select unit to Support");
    });

    test("aux step with Convoy order", () => {
        const order = { type: "Convoy" };
        const result = getStepLabel("aux", order);
        expect(result).toBe("Select unit to Convoy");
    });
});

describe("getOptions", () => {
    const mockVariant = {
        provinces: [
            { id: "tri", name: "Trieste" },
            { id: "vie", name: "Vienna" },
            { id: "bul", name: "Bulgaria" },
            { id: "bud", name: "Budapest" },
            { id: "ser", name: "Serbia" },
            { id: "rum", name: "Rumania" },
            { id: "adr", name: "Adriatic Sea" },
            { id: "alb", name: "Albania" },
            { id: "ven", name: "Venice" },
            { id: "gal", name: "Galicia" },
            { id: "tri", name: "Trieste" },
            { id: "vie", name: "Vienna" },
            { id: "boh", name: "Bohemia" },
            { id: "mun", name: "Munich" },
            { id: "war", name: "Warsaw" },
            { id: "sev", name: "Sevastopol" },

        ]
    } as unknown as Variant;

    const mockPhase = {
        units: [
            { province: { id: "bud" }, type: "Army" },
            { province: { id: "tri" }, type: "Fleet" },
            { province: { id: "vie" }, type: "Army" },
        ]
    } as unknown as Phase;

    const options = {
        "bud": {
            "Next": {
                "Hold": {
                    "Next": {
                        "bud": {
                            "Next": {},
                            "Type": "SrcProvince"
                        }
                    },
                    "Type": "OrderType"
                },
                "Move": {
                    "Next": {
                        "bud": {
                            "Next": {
                                "gal": {
                                    "Next": {},
                                    "Type": "Province"
                                },
                                "rum": {
                                    "Next": {},
                                    "Type": "Province"
                                },
                                "ser": {
                                    "Next": {},
                                    "Type": "Province"
                                },
                                "tri": {
                                    "Next": {},
                                    "Type": "Province"
                                },
                                "vie": {
                                    "Next": {},
                                    "Type": "Province"
                                }
                            },
                            "Type": "SrcProvince"
                        }
                    },
                    "Type": "OrderType"
                },
                "Support": {
                    "Next": {
                        "bud": {
                            "Next": {
                                "sev": {
                                    "Next": {
                                        "rum": {
                                            "Next": {},
                                            "Type": "Province"
                                        }
                                    },
                                    "Type": "Province"
                                },
                                "tri": {
                                    "Next": {
                                        "tri": {
                                            "Next": {},
                                            "Type": "Province"
                                        }
                                    },
                                    "Type": "Province"
                                },
                                "ven": {
                                    "Next": {
                                        "tri": {
                                            "Next": {},
                                            "Type": "Province"
                                        }
                                    },
                                    "Type": "Province"
                                },
                                "vie": {
                                    "Next": {
                                        "gal": {
                                            "Next": {},
                                            "Type": "Province"
                                        },
                                        "tri": {
                                            "Next": {},
                                            "Type": "Province"
                                        },
                                        "vie": {
                                            "Next": {},
                                            "Type": "Province"
                                        }
                                    },
                                    "Type": "Province"
                                },
                                "war": {
                                    "Next": {
                                        "gal": {
                                            "Next": {},
                                            "Type": "Province"
                                        }
                                    },
                                    "Type": "Province"
                                }
                            },
                            "Type": "SrcProvince"
                        }
                    },
                    "Type": "OrderType"
                }
            },
            "Type": "Province"
        },
        "tri": {
            "Next": {
                "Hold": {
                    "Next": {
                        "tri": {
                            "Next": {},
                            "Type": "SrcProvince"
                        }
                    },
                    "Type": "OrderType"
                },
                "Move": {
                    "Next": {
                        "tri": {
                            "Next": {
                                "adr": {
                                    "Next": {},
                                    "Type": "Province"
                                },
                                "alb": {
                                    "Next": {},
                                    "Type": "Province"
                                },
                                "ven": {
                                    "Next": {},
                                    "Type": "Province"
                                }
                            },
                            "Type": "SrcProvince"
                        }
                    },
                    "Type": "OrderType"
                },
                "Support": {
                    "Next": {
                        "tri": {
                            "Next": {
                                "rom": {
                                    "Next": {
                                        "ven": {
                                            "Next": {},
                                            "Type": "Province"
                                        }
                                    },
                                    "Type": "Province"
                                },
                                "ven": {
                                    "Next": {
                                        "ven": {
                                            "Next": {},
                                            "Type": "Province"
                                        }
                                    },
                                    "Type": "Province"
                                }
                            },
                            "Type": "SrcProvince"
                        }
                    },
                    "Type": "OrderType"
                }
            },
            "Type": "Province"
        },
        "vie": {
            "Next": {
                "Hold": {
                    "Next": {
                        "vie": {
                            "Next": {},
                            "Type": "SrcProvince"
                        }
                    },
                    "Type": "OrderType"
                },
                "Move": {
                    "Next": {
                        "vie": {
                            "Next": {
                                "boh": {
                                    "Next": {},
                                    "Type": "Province"
                                },
                                "bud": {
                                    "Next": {},
                                    "Type": "Province"
                                },
                                "gal": {
                                    "Next": {},
                                    "Type": "Province"
                                },
                                "tri": {
                                    "Next": {},
                                    "Type": "Province"
                                },
                                "tyr": {
                                    "Next": {},
                                    "Type": "Province"
                                }
                            },
                            "Type": "SrcProvince"
                        }
                    },
                    "Type": "OrderType"
                },
                "Support": {
                    "Next": {
                        "vie": {
                            "Next": {
                                "bud": {
                                    "Next": {
                                        "bud": {
                                            "Next": {},
                                            "Type": "Province"
                                        },
                                        "gal": {
                                            "Next": {},
                                            "Type": "Province"
                                        },
                                        "tri": {
                                            "Next": {},
                                            "Type": "Province"
                                        }
                                    },
                                    "Type": "Province"
                                },
                                "mun": {
                                    "Next": {
                                        "boh": {
                                            "Next": {},
                                            "Type": "Province"
                                        },
                                        "tyr": {
                                            "Next": {},
                                            "Type": "Province"
                                        }
                                    },
                                    "Type": "Province"
                                },
                                "tri": {
                                    "Next": {
                                        "tri": {
                                            "Next": {},
                                            "Type": "Province"
                                        }
                                    },
                                    "Type": "Province"
                                },
                                "ven": {
                                    "Next": {
                                        "tri": {
                                            "Next": {},
                                            "Type": "Province"
                                        },
                                        "tyr": {
                                            "Next": {},
                                            "Type": "Province"
                                        }
                                    },
                                    "Type": "Province"
                                },
                                "war": {
                                    "Next": {
                                        "gal": {
                                            "Next": {},
                                            "Type": "Province"
                                        }
                                    },
                                    "Type": "Province"
                                }
                            },
                            "Type": "SrcProvince"
                        }
                    },
                    "Type": "OrderType"
                }
            },
            "Type": "Province"
        }

    }

    test("no source", () => {
        const order = {};
        const result = getOptions(order, options, mockVariant);
        expect(result).toEqual([{
            key: "bud",
            label: "Budapest",
        },
        {
            key: "tri",
            label: "Trieste",
        },
        {
            key: "vie",
            label: "Vienna",
        }
        ]);
    })
    test("source is bud", () => {
        const order = { source: "bud" };
        const result = getOptions(order, options, mockVariant);
        expect(result).toEqual([
            {
                key: "Hold",
                label: "Hold",
            },
            {
                key: "Move",
                label: "Move",
            },
            {
                key: "Support",
                label: "Support",
            },
        ]);
    });
    test("source is bud, type is hold", () => {
        const order = { source: "bud", type: "Hold" };
        const result = getOptions(order, options, mockVariant);
        expect(result).toEqual([]);
    })
    test("source is bud, type is move", () => {
        const order = { source: "bud", type: "Move" };
        const result = getOptions(order, options, mockVariant);
        expect(result).toEqual([
            {
                key: "gal",
                label: "Galicia",
            },
            {
                key: "rum",
                label: "Rumania",
            },
            {
                key: "ser",
                label: "Serbia",
            },
            {
                key: "tri",
                label: "Trieste",
            },
            {
                key: "vie",
                label: "Vienna",
            }
        ]);
    })
    test("source is bud, type is move, target is gal", () => {
        const order = { source: "bud", type: "Move", target: "gal" };
        const result = getOptions(order, options, mockVariant);
        expect(result).toEqual([]);
    })
    test("source is bud, type is support", () => {
        const order = { source: "bud", type: "Support" };
        const result = getOptions(order, options, mockVariant);
        expect(result).toEqual([
            {
                key: "sev",
                label: "Sevastopol",
            },
            {
                key: "tri",
                label: "Trieste",
            },
            {
                key: "ven",
                label: "Venice",
            },
            {
                key: "vie",
                label: "Vienna",
            },
            {
                key: "war",
                label: "Warsaw",
            }
        ])
    })
    test("source is bud, type is support, aux is sev", () => {
        const order = { source: "bud", type: "Support", aux: "sev" };
        const result = getOptions(order, options, mockVariant);
        expect(result).toEqual([
            {
                key: "rum",
                label: "Rumania",
            },
        ]);
    })
    test("source is bud, type is support, aux is sev, target is rum", () => {
        const order = { source: "bud", type: "Support", aux: "sev", target: "rum" };
        const result = getOptions(order, options, mockVariant);
        expect(result).toEqual([]);
    })
    test("source is bud, type is support, aux is vie", () => {
        const order = { source: "bud", type: "Support", aux: "vie" };
        const result = getOptions(order, options, mockVariant);
        expect(result).toEqual([
            {
                key: "gal",
                label: "Galicia",
            },
            {
                key: "tri",
                label: "Trieste",
            },
            {
                key: "vie",
                label: "Vienna",
            },
        ])
    })
    test("source is tri", () => {
        const order = { source: "tri" };
        const result = getOptions(order, options, mockVariant);
        expect(result).toEqual([
            {
                key: "Hold",
                label: "Hold",
            },
            {
                key: "Move",
                label: "Move",
            },
            {
                key: "Support",
                label: "Support",
            },
        ]);
    });
    test("source is vie", () => {
        const order = { source: "vie" };
        const result = getOptions(order, options, mockVariant);
        expect(result).toEqual([
            {
                key: "Hold",
                label: "Hold",
            },
            {
                key: "Move",
                label: "Move",
            },
            {
                key: "Support",
                label: "Support",
            },
        ]);
    });
})

