import service, { phaseSchema, extractPropertiesList, listApiResponseSchema } from "../store/service";

const startedGame: typeof service.endpoints.listPhases.Types.ResultType = extractPropertiesList(listApiResponseSchema(phaseSchema).parse(
    {
        "Name": "phases",
        "Properties": [
            {
                "Name": "Spring 1901, Movement",
                "Properties": {
                    "PhaseOrdinal": 1,
                    "Season": "Spring",
                    "Year": 1901,
                    "Type": "Movement",
                    "Resolved": true,
                    "CreatedAt": "2024-12-19T15:11:15.667614Z",
                    "CreatedAgo": -342329119738838,
                    "ResolvedAt": "2024-12-20T15:11:15.924866Z",
                    "ResolvedAgo": -255928862486928,
                    "DeadlineAt": "2024-12-20T15:11:15.667614Z",
                    "NextDeadlineIn": -255929119738348,
                    "UnitsJSON": "",
                    "SCsJSON": "",
                    "GameID": "ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM",
                    "Units": [
                        {
                            "Province": "mar",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "tri",
                            "Unit": {
                                "Type": "Fleet",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "vie",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "bud",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "bre",
                            "Unit": {
                                "Type": "Fleet",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "par",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "France"
                            }
                        }
                    ],
                    "SCs": [
                        {
                            "Province": "bud",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "bre",
                            "Owner": "France"
                        },
                        {
                            "Province": "par",
                            "Owner": "France"
                        },
                        {
                            "Province": "mar",
                            "Owner": "France"
                        },
                        {
                            "Province": "tri",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "vie",
                            "Owner": "Austria"
                        }
                    ],
                    "Dislodgeds": null,
                    "Dislodgers": null,
                    "ForceDisbands": null,
                    "Bounces": null,
                    "Resolutions": [
                        {
                            "Province": "bud",
                            "Resolution": "OK"
                        },
                        {
                            "Province": "tri",
                            "Resolution": "OK"
                        },
                        {
                            "Province": "vie",
                            "Resolution": "OK"
                        },
                        {
                            "Province": "bre",
                            "Resolution": "OK"
                        },
                        {
                            "Province": "par",
                            "Resolution": "OK"
                        },
                        {
                            "Province": "mar",
                            "Resolution": "OK"
                        }
                    ],
                    "Host": "diplicity-engine.appspot.com",
                    "SoloSCCount": 0,
                    "PreliminaryScores": [
                        {
                            "UserId": "",
                            "Member": "Austria",
                            "SCs": 3,
                            "Score": 50,
                            "Explanation": "Survival:33\nSupply centers:17\nTribute:0"
                        },
                        {
                            "UserId": "",
                            "Member": "France",
                            "SCs": 3,
                            "Score": 50,
                            "Explanation": "Survival:33\nSupply centers:17\nTribute:0"
                        }
                    ]
                },
                "Type": "Phase",
                "Links": [
                    {
                        "Rel": "self",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/1",
                        "Method": "GET"
                    },
                    {
                        "Rel": "map",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/1/Map",
                        "Method": "GET"
                    },
                    {
                        "Rel": "orders",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/1/Orders",
                        "Method": "GET"
                    },
                    {
                        "Rel": "corroborate",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/1/Corroborate",
                        "Method": "GET"
                    },
                    {
                        "Rel": "phase-states",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/1/PhaseStates",
                        "Method": "GET"
                    },
                    {
                        "Rel": "phase-result",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/1/Result",
                        "Method": "GET"
                    }
                ]
            },
            {
                "Name": "Spring 1901, Retreat",
                "Properties": {
                    "PhaseOrdinal": 2,
                    "Season": "Spring",
                    "Year": 1901,
                    "Type": "Retreat",
                    "Resolved": true,
                    "CreatedAt": "2024-12-20T15:11:15.927981Z",
                    "CreatedAgo": -255928859383033,
                    "ResolvedAt": "2024-12-20T15:11:15.991966Z",
                    "ResolvedAgo": -255928795398113,
                    "DeadlineAt": "2024-12-20T15:11:15.938008Z",
                    "NextDeadlineIn": -255928849355953,
                    "UnitsJSON": "",
                    "SCsJSON": "",
                    "GameID": "ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM",
                    "Units": [
                        {
                            "Province": "ser",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "bre",
                            "Unit": {
                                "Type": "Fleet",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "par",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "mar",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "tri",
                            "Unit": {
                                "Type": "Fleet",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "vie",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "Austria"
                            }
                        }
                    ],
                    "SCs": [
                        {
                            "Province": "bre",
                            "Owner": "France"
                        },
                        {
                            "Province": "par",
                            "Owner": "France"
                        },
                        {
                            "Province": "mar",
                            "Owner": "France"
                        },
                        {
                            "Province": "tri",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "vie",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "bud",
                            "Owner": "Austria"
                        }
                    ],
                    "Dislodgeds": null,
                    "Dislodgers": null,
                    "ForceDisbands": null,
                    "Bounces": null,
                    "Resolutions": null,
                    "Host": "diplicity-engine.appspot.com",
                    "SoloSCCount": 18,
                    "PreliminaryScores": [
                        {
                            "UserId": "",
                            "Member": "Austria",
                            "SCs": 3,
                            "Score": 50,
                            "Explanation": "Survival:33\nSupply centers:17\nTribute:0"
                        },
                        {
                            "UserId": "",
                            "Member": "France",
                            "SCs": 3,
                            "Score": 50,
                            "Explanation": "Survival:33\nSupply centers:17\nTribute:0"
                        }
                    ]
                },
                "Type": "Phase",
                "Links": [
                    {
                        "Rel": "self",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/2",
                        "Method": "GET"
                    },
                    {
                        "Rel": "map",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/2/Map",
                        "Method": "GET"
                    },
                    {
                        "Rel": "orders",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/2/Orders",
                        "Method": "GET"
                    },
                    {
                        "Rel": "corroborate",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/2/Corroborate",
                        "Method": "GET"
                    },
                    {
                        "Rel": "phase-states",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/2/PhaseStates",
                        "Method": "GET"
                    },
                    {
                        "Rel": "phase-result",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/2/Result",
                        "Method": "GET"
                    }
                ]
            },
            {
                "Name": "Fall 1901, Movement",
                "Properties": {
                    "PhaseOrdinal": 3,
                    "Season": "Fall",
                    "Year": 1901,
                    "Type": "Movement",
                    "Resolved": true,
                    "CreatedAt": "2024-12-20T15:11:15.995562Z",
                    "CreatedAgo": -255928791804584,
                    "ResolvedAt": "2024-12-21T15:11:16.178856Z",
                    "ResolvedAgo": -169528608510654,
                    "DeadlineAt": "2024-12-21T15:11:15.995562Z",
                    "NextDeadlineIn": -169528791804514,
                    "UnitsJSON": "",
                    "SCsJSON": "",
                    "GameID": "ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM",
                    "Units": [
                        {
                            "Province": "ser",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "bre",
                            "Unit": {
                                "Type": "Fleet",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "par",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "mar",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "tri",
                            "Unit": {
                                "Type": "Fleet",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "vie",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "Austria"
                            }
                        }
                    ],
                    "SCs": [
                        {
                            "Province": "mar",
                            "Owner": "France"
                        },
                        {
                            "Province": "tri",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "vie",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "bud",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "bre",
                            "Owner": "France"
                        },
                        {
                            "Province": "par",
                            "Owner": "France"
                        }
                    ],
                    "Dislodgeds": null,
                    "Dislodgers": null,
                    "ForceDisbands": null,
                    "Bounces": null,
                    "Resolutions": [
                        {
                            "Province": "ser",
                            "Resolution": "OK"
                        },
                        {
                            "Province": "vie",
                            "Resolution": "OK"
                        },
                        {
                            "Province": "bre",
                            "Resolution": "OK"
                        },
                        {
                            "Province": "par",
                            "Resolution": "OK"
                        },
                        {
                            "Province": "mar",
                            "Resolution": "OK"
                        },
                        {
                            "Province": "tri",
                            "Resolution": "OK"
                        }
                    ],
                    "Host": "diplicity-engine.appspot.com",
                    "SoloSCCount": 18,
                    "PreliminaryScores": [
                        {
                            "UserId": "",
                            "Member": "Austria",
                            "SCs": 3,
                            "Score": 50,
                            "Explanation": "Survival:33\nSupply centers:17\nTribute:0"
                        },
                        {
                            "UserId": "",
                            "Member": "France",
                            "SCs": 3,
                            "Score": 50,
                            "Explanation": "Survival:33\nSupply centers:17\nTribute:0"
                        }
                    ]
                },
                "Type": "Phase",
                "Links": [
                    {
                        "Rel": "self",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/3",
                        "Method": "GET"
                    },
                    {
                        "Rel": "map",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/3/Map",
                        "Method": "GET"
                    },
                    {
                        "Rel": "orders",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/3/Orders",
                        "Method": "GET"
                    },
                    {
                        "Rel": "corroborate",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/3/Corroborate",
                        "Method": "GET"
                    },
                    {
                        "Rel": "phase-states",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/3/PhaseStates",
                        "Method": "GET"
                    },
                    {
                        "Rel": "phase-result",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/3/Result",
                        "Method": "GET"
                    }
                ]
            },
            {
                "Name": "Fall 1901, Retreat",
                "Properties": {
                    "PhaseOrdinal": 4,
                    "Season": "Fall",
                    "Year": 1901,
                    "Type": "Retreat",
                    "Resolved": true,
                    "CreatedAt": "2024-12-21T15:11:16.182146Z",
                    "CreatedAgo": -169528605222585,
                    "ResolvedAt": "2024-12-21T15:11:16.204495Z",
                    "ResolvedAgo": -169528582873665,
                    "DeadlineAt": "2024-12-21T15:11:16.194931Z",
                    "NextDeadlineIn": -169528592437515,
                    "UnitsJSON": "",
                    "SCsJSON": "",
                    "GameID": "ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM",
                    "Units": [
                        {
                            "Province": "par",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "mar",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "tri",
                            "Unit": {
                                "Type": "Fleet",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "vie",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "bul",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "bre",
                            "Unit": {
                                "Type": "Fleet",
                                "Nation": "France"
                            }
                        }
                    ],
                    "SCs": [
                        {
                            "Province": "tri",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "vie",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "bud",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "bre",
                            "Owner": "France"
                        },
                        {
                            "Province": "par",
                            "Owner": "France"
                        },
                        {
                            "Province": "mar",
                            "Owner": "France"
                        }
                    ],
                    "Dislodgeds": null,
                    "Dislodgers": null,
                    "ForceDisbands": null,
                    "Bounces": null,
                    "Resolutions": null,
                    "Host": "diplicity-engine.appspot.com",
                    "SoloSCCount": 18,
                    "PreliminaryScores": [
                        {
                            "UserId": "",
                            "Member": "Austria",
                            "SCs": 3,
                            "Score": 50,
                            "Explanation": "Survival:33\nSupply centers:17\nTribute:0"
                        },
                        {
                            "UserId": "",
                            "Member": "France",
                            "SCs": 3,
                            "Score": 50,
                            "Explanation": "Survival:33\nSupply centers:17\nTribute:0"
                        }
                    ]
                },
                "Type": "Phase",
                "Links": [
                    {
                        "Rel": "self",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/4",
                        "Method": "GET"
                    },
                    {
                        "Rel": "map",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/4/Map",
                        "Method": "GET"
                    },
                    {
                        "Rel": "orders",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/4/Orders",
                        "Method": "GET"
                    },
                    {
                        "Rel": "corroborate",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/4/Corroborate",
                        "Method": "GET"
                    },
                    {
                        "Rel": "phase-states",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/4/PhaseStates",
                        "Method": "GET"
                    },
                    {
                        "Rel": "phase-result",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/4/Result",
                        "Method": "GET"
                    }
                ]
            },
            {
                "Name": "Fall 1901, Adjustment",
                "Properties": {
                    "PhaseOrdinal": 5,
                    "Season": "Fall",
                    "Year": 1901,
                    "Type": "Adjustment",
                    "Resolved": true,
                    "CreatedAt": "2024-12-21T15:11:16.207432Z",
                    "CreatedAgo": -169528579938576,
                    "ResolvedAt": "2024-12-22T15:11:16.407837Z",
                    "ResolvedAgo": -83128379533646,
                    "DeadlineAt": "2024-12-22T15:11:16.207432Z",
                    "NextDeadlineIn": -83128579938436,
                    "UnitsJSON": "",
                    "SCsJSON": "",
                    "GameID": "ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM",
                    "Units": [
                        {
                            "Province": "tri",
                            "Unit": {
                                "Type": "Fleet",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "vie",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "bul",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "bre",
                            "Unit": {
                                "Type": "Fleet",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "par",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "mar",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "France"
                            }
                        }
                    ],
                    "SCs": [
                        {
                            "Province": "mar",
                            "Owner": "France"
                        },
                        {
                            "Province": "bul",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "tri",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "vie",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "bud",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "bre",
                            "Owner": "France"
                        },
                        {
                            "Province": "par",
                            "Owner": "France"
                        }
                    ],
                    "Dislodgeds": null,
                    "Dislodgers": null,
                    "ForceDisbands": null,
                    "Bounces": null,
                    "Resolutions": null,
                    "Host": "diplicity-engine.appspot.com",
                    "SoloSCCount": 18,
                    "PreliminaryScores": [
                        {
                            "UserId": "",
                            "Member": "Austria",
                            "SCs": 4,
                            "Score": 52.42857142857143,
                            "Explanation": "Survival:33\nSupply centers:19.428571428571427\nTribute:0"
                        },
                        {
                            "UserId": "",
                            "Member": "France",
                            "SCs": 3,
                            "Score": 47.57142857142857,
                            "Explanation": "Survival:33\nSupply centers:14.57142857142857\nTribute:-0"
                        }
                    ]
                },
                "Type": "Phase",
                "Links": [
                    {
                        "Rel": "self",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/5",
                        "Method": "GET"
                    },
                    {
                        "Rel": "map",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/5/Map",
                        "Method": "GET"
                    },
                    {
                        "Rel": "orders",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/5/Orders",
                        "Method": "GET"
                    },
                    {
                        "Rel": "corroborate",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/5/Corroborate",
                        "Method": "GET"
                    },
                    {
                        "Rel": "phase-states",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/5/PhaseStates",
                        "Method": "GET"
                    },
                    {
                        "Rel": "phase-result",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/5/Result",
                        "Method": "GET"
                    }
                ]
            },
            {
                "Name": "Spring 1902, Movement",
                "Properties": {
                    "PhaseOrdinal": 6,
                    "Season": "Spring",
                    "Year": 1902,
                    "Type": "Movement",
                    "Resolved": true,
                    "CreatedAt": "2024-12-22T15:11:16.414008Z",
                    "CreatedAgo": -83128373366077,
                    "ResolvedAt": "2024-12-22T15:11:16.421787Z",
                    "ResolvedAgo": -83128365587167,
                    "DeadlineAt": "2024-12-23T15:11:16.414008Z",
                    "NextDeadlineIn": 3271626634033,
                    "UnitsJSON": "",
                    "SCsJSON": "",
                    "GameID": "ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM",
                    "Units": [
                        {
                            "Province": "mar",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "tri",
                            "Unit": {
                                "Type": "Fleet",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "vie",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "bul",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "Austria"
                            }
                        },
                        {
                            "Province": "bre",
                            "Unit": {
                                "Type": "Fleet",
                                "Nation": "France"
                            }
                        },
                        {
                            "Province": "par",
                            "Unit": {
                                "Type": "Army",
                                "Nation": "France"
                            }
                        }
                    ],
                    "SCs": [
                        {
                            "Province": "bud",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "bre",
                            "Owner": "France"
                        },
                        {
                            "Province": "par",
                            "Owner": "France"
                        },
                        {
                            "Province": "mar",
                            "Owner": "France"
                        },
                        {
                            "Province": "bul",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "tri",
                            "Owner": "Austria"
                        },
                        {
                            "Province": "vie",
                            "Owner": "Austria"
                        }
                    ],
                    "Dislodgeds": null,
                    "Dislodgers": null,
                    "ForceDisbands": null,
                    "Bounces": null,
                    "Resolutions": null,
                    "Host": "diplicity-engine.appspot.com",
                    "SoloSCCount": 18,
                    "PreliminaryScores": [
                        {
                            "UserId": "",
                            "Member": "Austria",
                            "SCs": 4,
                            "Score": 52.42857142857143,
                            "Explanation": "Survival:33\nSupply centers:19.428571428571427\nTribute:0"
                        },
                        {
                            "UserId": "",
                            "Member": "France",
                            "SCs": 3,
                            "Score": 47.57142857142857,
                            "Explanation": "Survival:33\nSupply centers:14.57142857142857\nTribute:-0"
                        }
                    ]
                },
                "Type": "Phase",
                "Links": [
                    {
                        "Rel": "self",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/6",
                        "Method": "GET"
                    },
                    {
                        "Rel": "map",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/6/Map",
                        "Method": "GET"
                    },
                    {
                        "Rel": "orders",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/6/Orders",
                        "Method": "GET"
                    },
                    {
                        "Rel": "corroborate",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/6/Corroborate",
                        "Method": "GET"
                    },
                    {
                        "Rel": "phase-states",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/6/PhaseStates",
                        "Method": "GET"
                    },
                    {
                        "Rel": "phase-result",
                        "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phase/6/Result",
                        "Method": "GET"
                    }
                ]
            }
        ],
        "Type": "List",
        "Links": [
            {
                "Rel": "self",
                "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phases",
                "Method": "GET"
            }
        ]
    }
));

export { startedGame };