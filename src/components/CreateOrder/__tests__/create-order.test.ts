import { createOrderOptionTree, getNextOptionsNode, getOptionAtIndex, getOrderStatus } from "../CreateOrder.util";

const options = {
    "bul": {
        "Next": {
            "Hold": {
                "Next": {
                    "bul": {
                        "Next": {},
                        "Type": "SrcProvince"
                    }
                },
                "Type": "OrderType"
            },
            "Move": {
                "Next": {
                    "bul": {
                        "Next": {
                            "con": {
                                "Next": {},
                                "Type": "Province"
                            },
                            "gre": {
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
}

const variant = {
    getProvinceLongName: (key: string) => key
} as Parameters<typeof createOrderOptionTree>[0];

const transformedOptions = createOrderOptionTree(variant, options);

test("transforms options correctly", () => {
    const expected = {
        "bul": {
            "name": "bul",
            "children": {
                "Hold": {
                    "name": "Hold",
                    "children": {}
                },
                "Move": {
                    "name": "Move",
                    "children": {
                        "con": {
                            "name": "con",
                            "children": {}
                        },
                        "gre": {
                            "name": "gre",
                            "children": {}
                        },
                        "rum": {
                            "name": "rum",
                            "children": {}
                        },
                        "ser": {
                            "name": "ser",
                            "children": {}
                        }
                    }
                }
            }
        }
    };

    expect(transformedOptions).toEqual(expected);
});

test("getNextOptionsNode returns correct node when zero selected options", () => {
    const selectedOptions: string[] = [];
    const expected = transformedOptions;
    const actual = getNextOptionsNode(transformedOptions, selectedOptions);
    expect(actual).toEqual(expected);
});

test("getNextOptionsNode returns correct node when one selected option", () => {
    const selectedOptions = ["bul"];
    const expected = transformedOptions["bul"].children;
    const actual = getNextOptionsNode(transformedOptions, selectedOptions);
    expect(actual).toEqual(expected);
});

test("getNextOptionsNode returns correct node when two selected options", () => {
    const selectedOptions = ["bul", "Move"];
    const expected = transformedOptions["bul"].children["Move"].children;
    const actual = getNextOptionsNode(transformedOptions, selectedOptions);
    expect(actual).toEqual(expected);
});

test("getOptionAtIndex returns correct option when index is 0 and selectedOption is correct", () => {
    const selectedOptions = ["bul"];
    const expected = "bul"
    const actual = getOptionAtIndex(transformedOptions, selectedOptions, 0);
    expect(actual?.name).toEqual(expected);
});

test("getOptionAtIndex returns correct option when index is 1 and selectedOption is correct", () => {
    const selectedOptions = ["bul", "Move"];
    const expected = "Move"
    const actual = getOptionAtIndex(transformedOptions, selectedOptions, 1);
    expect(actual?.name).toEqual(expected);
});

test("getOptionAtIndex returns correct option when index is 2 and selectedOption is correct", () => {
    const selectedOptions = ["bul", "Move", "con"];
    const expected = "con"
    const actual = getOptionAtIndex(transformedOptions, selectedOptions, 2);
    expect(actual?.name).toEqual(expected);
});

test("getOrderStatus returns correct status when zero selected options", () => {
    const selectedOptions: string[] = [];
    const expected = {
        source: undefined,
        orderType: undefined,
        target: undefined,
        aux: undefined,
        isComplete: false
    };
    const actual = getOrderStatus(transformedOptions, selectedOptions);
    expect(actual).toEqual(expected);
});

test("getOrderStatus returns correct status when one selected option", () => {
    const selectedOptions = ["bul"];
    const expected = {
        source: expect.objectContaining({ name: "bul" }),
        orderType: undefined,
        target: undefined,
        aux: undefined,
        isComplete: false
    };
    const actual = getOrderStatus(transformedOptions, selectedOptions);
    expect(actual).toEqual(expected);
});

test("getOrderStatus returns correct status when two selected options", () => {
    const selectedOptions = ["bul", "Move"];
    const expected = {
        source: expect.objectContaining({ name: "bul" }),
        orderType: expect.objectContaining({ name: "Move" }),
        target: undefined,
        aux: undefined,
        isComplete: false
    };
    const actual = getOrderStatus(transformedOptions, selectedOptions);
    expect(actual).toEqual(expected);
});

test("getOrderStatus returns correct status when three selected options", () => {
    const selectedOptions = ["bul", "Move", "con"];
    const expected = {
        source: expect.objectContaining({ name: "bul" }),
        orderType: expect.objectContaining({ name: "Move" }),
        target: expect.objectContaining({ name: "con" }),
        aux: undefined,
        isComplete: true
    };
    const actual = getOrderStatus(transformedOptions, selectedOptions);
    expect(actual).toEqual(expected);
});