import service, { extractProperties } from "../store/service";

const startedGame: typeof service.endpoints.listOptions.Types.ResultType = extractProperties({
    "Name": "options",
    "Properties": {
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
    },
    "Desc": [
        [
            "Options explained",
            "The options consist of a decision tree where each node represents a decision a player has to make when defining an order.",
            "Each child set contains one or more alternatives of the same decision type, viz. `Province`, `OrderType`, `UnitType` or `SrcProvince`.",
            "To guide the player towards defining an order, present the alternatives for each node, then the sub tree pointed to by `Next`, etc. until a leaf node is reached.",
            "When a leaf is reached, the value nodes between root and leaf contain the list of strings defining an order the server will understand."
        ],
        [
            "Province",
            "`Province` decisions represent picking a province from the game map.",
            "The children of the root of the options tree indicate that the user needs to select which province to define an order for.",
            "The first `Province` option just indicates which province the order is meant for."
        ],
        [
            "OrderType",
            "`OrderType` decisions represent picking a type of order for a province."
        ],
        [
            "UnitType",
            "`UnitType` decisions represent picking a type of unit for an order."
        ],
        [
            "SrcProvince",
            "`SrcProvince` indicates that the value should replace the first `Province` value in the order list without presenting the player with a choice.",
            "This is useful e.g. when the order has a coast as source province, but the click should be accepted in the entire province."
        ]
    ],
    "Type": "",
    "Links": [
        {
            "Rel": "self",
            "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/6/Options",
            "Method": "GET"
        }
    ]
})

export { startedGame }
