import { expect, test } from 'vitest'
import { getOptions } from '../order'
import { Options } from '../../store/service.types'

const testOptions: Options = {
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
                            "tri": {
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
                            "tri": {
                                "Next": {
                                    "tri": {
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

test("Returns source province names when selected options is empty", () => {
    const { options } = getOptions(testOptions, [])
    expect(options).toEqual(["bud", "tri", "vie"])
})

test("Returns correct type when selected options is empty", () => {
    const { type } = getOptions(testOptions, [])
    expect(type).toEqual("Province")
})

test("Returns order types when selected options is a province", () => {
    const { options } = getOptions(testOptions, ["bud"])
    expect(options).toEqual(["Hold", "Move", "Support"])
})

test("Returns correct type when selected options is a province", () => {
    const { type } = getOptions(testOptions, ["bud"])
    expect(type).toEqual("OrderType")
})

test("Returns source province names when selected options is a province and an order type", () => {
    const { options } = getOptions(testOptions, ["bud", "Move"])
    expect(options).toEqual(["bud"])
})

test("Returns correct type when selected options is a province and an order type", () => {
    const { type } = getOptions(testOptions, ["bud", "Move"])
    expect(type).toEqual("SrcProvince")
})

test("Returns destination province names when selected options is a province, an order type and a source province", () => {
    const { options } = getOptions(testOptions, ["bud", "Move", "bud"])
    expect(options).toEqual(["gal", "rum", "ser", "tri", "vie"])
})

test("Returns correct type when selected options is a province, an order type and a source province", () => {
    const { type } = getOptions(testOptions, ["bud", "Move", "bud"])
    expect(type).toEqual("Province")
})

test("Returns empty options and undefined type when move order is complete", () => {
    const { options, type } = getOptions(testOptions, ["bud", "Move", "bud", "gal"])
    expect(options).toEqual([]);
    expect(type).toEqual(undefined);
})

test("Returns empty options and undefined type when hold order is complete", () => {
    const { options, type } = getOptions(testOptions, ["bud", "Hold", "bud"])
    expect(options).toEqual([]);
    expect(type).toEqual(undefined);
})

test("Returns empty options and undefined type when support order is complete", () => {
    const { options, type } = getOptions(testOptions, ["bud", "Support", "bud", "tri", "tri"])
    expect(options).toEqual([]);
    expect(type).toEqual(undefined);
})

test("Throws expection when selected options is invalid", () => {
    expect(() => getOptions(testOptions, ["bud", "Hold", "bud", "gal"])).toThrowError("Invalid selected options")
})

test("Throws expection when selected options is invalid", () => {
    expect(() => getOptions(testOptions, ["mun"])).toThrowError("Invalid selected options")
})


