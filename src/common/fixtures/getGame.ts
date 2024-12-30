import service, { apiResponseSchema, gameSchema, extractProperties } from "../store/service";

const startedGame: typeof service.endpoints.getGame.Types.ResultType = extractProperties(apiResponseSchema(gameSchema).parse(
    {
        "Name": "Test game 1",
        "Properties": {
            "ID": "ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM",
            "Started": true,
            "Mustered": true,
            "Closed": true,
            "Finished": true,
            "Desc": "Test game 1",
            "Variant": "France vs Austria",
            "PhaseLengthMinutes": 1440,
            "NonMovementPhaseLengthMinutes": 0,
            "MaxHated": 0,
            "MaxHater": 0,
            "MinRating": 0,
            "MaxRating": 0,
            "MinReliability": 0,
            "MinQuickness": 0,
            "Private": false,
            "NoMerge": false,
            "DisableConferenceChat": false,
            "DisableGroupChat": false,
            "DisablePrivateChat": false,
            "NationAllocation": 0,
            "Anonymous": false,
            "LastYear": 0,
            "SkipMuster": true,
            "ChatLanguageISO639_1": "",
            "GameMasterEnabled": false,
            "RequireGameMasterInvitation": false,
            "DiscordWebhooks": {
                "GameStarted": {
                    "Id": "",
                    "Token": ""
                },
                "PhaseStarted": {
                    "Id": "",
                    "Token": ""
                }
            },
            "GameMasterInvitations": null,
            "GameMaster": {
                "Email": "",
                "FamilyName": "",
                "Gender": "",
                "GivenName": "",
                "Hd": "",
                "Id": "",
                "Link": "",
                "Locale": "",
                "Name": "",
                "Picture": "",
                "VerifiedEmail": false,
                "ValidUntil": "0001-01-01T00:00:00Z"
            },
            "NMembers": 2,
            "Members": [
                {
                    "User": {
                        "Email": "johnmcdowell0801@gmail.com",
                        "FamilyName": "McDowell",
                        "Gender": "",
                        "GivenName": "John",
                        "Hd": "",
                        "Id": "114413642839130335053",
                        "Link": "",
                        "Locale": "",
                        "Name": "John McDowell",
                        "Picture": "https://lh3.googleusercontent.com/a/ACg8ocKz-d2uUI4SbbRS_-tcbAcGovn6qvoha2lPsQVgKTll_zut=s96-c",
                        "VerifiedEmail": true,
                        "ValidUntil": "2024-12-20T14:15:08.790451Z"
                    },
                    "Nation": "Austria",
                    "GameAlias": "",
                    "NationPreferences": "",
                    "NewestPhaseState": {
                        "GameID": "ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM",
                        "PhaseOrdinal": 6,
                        "Nation": "Austria",
                        "ReadyToResolve": true,
                        "WantsDIAS": true,
                        "WantsConcede": false,
                        "OnProbation": true,
                        "NoOrders": false,
                        "Eliminated": false,
                        "Messages": "",
                        "ZippedOptions": "",
                        "Note": "Auto generated due to phase change at /Game,5069187172007936/5: wasReady = false, wantedDIAS = false, wantedConcede = false, onProbation = false, hadOrders = false, newOptionsCount = 3, wasEliminated = false"
                    },
                    "UnreadMessages": 6,
                    "Replaceable": false
                },
                {
                    "User": {
                        "Email": "",
                        "FamilyName": "User",
                        "Gender": "",
                        "GivenName": "Diplomacy",
                        "Hd": "",
                        "Id": "110407027004027825015",
                        "Link": "",
                        "Locale": "",
                        "Name": "Diplomacy User",
                        "Picture": "https://lh3.googleusercontent.com/a/ACg8ocKp8KHDwNjAs3pm2IUQN7bNgRte4E-NLjq18bYBi-sC3tWkog=s96-c",
                        "VerifiedEmail": true,
                        "ValidUntil": "2024-12-20T15:00:40.714338Z"
                    },
                    "Nation": "France",
                    "GameAlias": "",
                    "NationPreferences": "",
                    "NewestPhaseState": {
                        "GameID": null,
                        "PhaseOrdinal": 0,
                        "Nation": "",
                        "ReadyToResolve": false,
                        "WantsDIAS": false,
                        "WantsConcede": false,
                        "OnProbation": false,
                        "NoOrders": false,
                        "Eliminated": false,
                        "Messages": "",
                        "ZippedOptions": null,
                        "Note": ""
                    },
                    "UnreadMessages": 0,
                    "Replaceable": false
                }
            ],
            "StartETA": "2024-12-19T15:11:15.667586Z",
            "NewestPhaseMeta": [
                {
                    "PhaseOrdinal": 6,
                    "Season": "Spring",
                    "Year": 1902,
                    "Type": "Movement",
                    "Resolved": true,
                    "CreatedAt": "2024-12-22T15:11:16.414008Z",
                    "CreatedAgo": -82567555404012,
                    "ResolvedAt": "2024-12-22T15:11:16.421787Z",
                    "ResolvedAgo": -82567547625142,
                    "DeadlineAt": "2024-12-23T15:11:16.414008Z",
                    "NextDeadlineIn": 3832444596528,
                    "UnitsJSON": "[{\"Province\":\"mar\",\"Unit\":{\"Type\":\"Army\",\"Nation\":\"France\"}},{\"Province\":\"tri\",\"Unit\":{\"Type\":\"Fleet\",\"Nation\":\"Austria\"}},{\"Province\":\"vie\",\"Unit\":{\"Type\":\"Army\",\"Nation\":\"Austria\"}},{\"Province\":\"bul\",\"Unit\":{\"Type\":\"Army\",\"Nation\":\"Austria\"}},{\"Province\":\"bre\",\"Unit\":{\"Type\":\"Fleet\",\"Nation\":\"France\"}},{\"Province\":\"par\",\"Unit\":{\"Type\":\"Army\",\"Nation\":\"France\"}}]",
                    "SCsJSON": "[{\"Province\":\"bud\",\"Owner\":\"Austria\"},{\"Province\":\"bre\",\"Owner\":\"France\"},{\"Province\":\"par\",\"Owner\":\"France\"},{\"Province\":\"mar\",\"Owner\":\"France\"},{\"Province\":\"bul\",\"Owner\":\"Austria\"},{\"Province\":\"tri\",\"Owner\":\"Austria\"},{\"Province\":\"vie\",\"Owner\":\"Austria\"}]"
                }
            ],
            "ActiveBans": null,
            "FailedRequirements": null,
            "CreatedAt": "2024-12-19T15:10:08.744004Z",
            "CreatedAgo": -341835225408432,
            "StartedAt": "2024-12-19T15:11:15.667586Z",
            "StartedAgo": -341768301826522,
            "FinishedAt": "2024-12-22T15:11:16.421787Z",
            "FinishedAgo": -82567547625612
        },
        "Type": "Game",
        "Links": [
            {
                "Rel": "self",
                "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM",
                "Method": "GET"
            },
            {
                "Rel": "update-membership",
                "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Member/114413642839130335053",
                "Method": "PUT",
                "JSONSchema": {
                    "type": "object",
                    "properties": {
                        "GameAlias": {
                            "type": "string",
                            "title": "GameAlias"
                        },
                        "NationPreferences": {
                            "type": "string",
                            "title": "NationPreferences"
                        }
                    }
                }
            },
            {
                "Rel": "channels",
                "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Channels",
                "Method": "GET"
            },
            {
                "Rel": "phases",
                "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/Phases",
                "Method": "GET"
            },
            {
                "Rel": "game-result",
                "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/GameResult",
                "Method": "GET"
            },
            {
                "Rel": "game-states",
                "URL": "https://diplicity-engine.appspot.com/Game/ahJzfmRpcGxpY2l0eS1lbmdpbmVyEQsSBEdhbWUYgIDA5eHMgAkM/GameStates",
                "Method": "GET"
            }
        ]
    }
));

export { startedGame };