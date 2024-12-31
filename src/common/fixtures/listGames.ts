import { Game, GameStatus } from "../store/service.types";

const createGame = (id: string, status: GameStatus, title: string): Game => ({
    Anonymous: false,
    ChatLanguageISO639_1: "en",
    Desc: title,
    DisableConferenceChat: false,
    DisableGroupChat: false,
    DisablePrivateChat: false,
    FirstMember: {
        User: {
            Email: "test@example.com",
            FamilyName: "Doe",
            Gender: "Male",
            GivenName: "John",
            Hd: "example.com",
            Id: id,
            Link: "http://example.com",
            Locale: "en",
            Name: "John Doe",
            Picture: "http://example.com/picture.jpg",
            VerifiedEmail: true,
            ValidUntil: "2023-12-31T23:59:59Z",
        },
        Nation: "Nation1",
        GameAlias: "JohnDoe",
        NationPreferences: "Preference",
        UnreadMessages: 0,
        Replacable: false,
        NewestPhaseState: {
            GameID: id,
            PhaseOrdinal: 1,
            Nation: "Nation1",
            ReadyToResolve: false,
            WantsDIAS: false,
            WantsConcede: false,
            OnProbation: false,
            NoOrders: false,
            Eliminated: false,
            Messages: "",
            ZippedOptions: null,
            Note: "",
        },
    },
    GameMasterEnabled: false,
    LastYear: 1905,
    MaxHated: null,
    MaxHater: 0,
    MaxRating: 100,
    MinQuickness: 0,
    MinRating: 0,
    MinReliability: 0,
    NationAllocation: 1,
    NonMovementPhaseLengthMinutes: 1440,
    PhaseLengthMinutes: 1440,
    Private: false,
    RequireGameMasterInvitation: false,
    SkipMuster: false,
    Variant: "Classical",
    ActiveBans: null,
    Closed: false,
    CreatedAgo: 0,
    CreatedAt: "2023-01-01T00:00:00Z",
    FailedRequirements: null,
    Finished: status === GameStatus.Finished,
    FinishedAgo: 0,
    FinishedAt: status === GameStatus.Finished ? "2023-01-01T00:00:00Z" : "",
    GameMaster: {
        Email: "gm@example.com",
        FamilyName: "Smith",
        Gender: "Female",
        GivenName: "Jane",
        Hd: "example.com",
        Id: "2",
        Link: "http://example.com",
        Locale: "en",
        Name: "Jane Smith",
        Picture: "http://example.com/picture.jpg",
        VerifiedEmail: true,
        ValidUntil: "2023-12-31T23:59:59Z",
    },
    GameMasterInvitations: null,
    ID: id,
    Members: [
        {
            User: {
                Email: "test@example.com",
                FamilyName: "Doe",
                Gender: "Male",
                GivenName: "John",
                Hd: "example.com",
                Id: id,
                Link: "http://example.com",
                Locale: "en",
                Name: "John Doe",
                Picture: "http://example.com/picture.jpg",
                VerifiedEmail: true,
                ValidUntil: "2023-12-31T23:59:59Z",
            },
            Nation: "Nation1",
            GameAlias: "JohnDoe",
            NationPreferences: "Preference",
            UnreadMessages: 0,
            Replacable: false,
            NewestPhaseState: {
                GameID: id,
                PhaseOrdinal: 1,
                Nation: "Nation1",
                ReadyToResolve: false,
                WantsDIAS: false,
                WantsConcede: false,
                OnProbation: false,
                NoOrders: false,
                Eliminated: false,
                Messages: "",
                ZippedOptions: null,
                Note: "",
            },
        },
    ],
    Mustered: false,
    NMembers: 1,
    NewestPhaseMeta: null,
    NoMerge: false,
    StartETA: "",
    Started: status === GameStatus.Started,
    StartedAgo: 0,
    StartedAt: status === GameStatus.Started ? "2023-01-01T00:00:00Z" : "",
});

const games = {
    stagingGame1: createGame("1", GameStatus.Staging, "Staging Game 1"),
    stagingGame2: createGame("2", GameStatus.Staging, "Staging Game 2"),
    startedGame1: createGame("3", GameStatus.Started, "Started Game 1"),
    startedGame2: createGame("4", GameStatus.Started, "Started Game 2"),
    finishedGame1: createGame("5", GameStatus.Finished, "Finished Game 1"),
    finishedGame2: createGame("6", GameStatus.Finished, "Finished Game 2"),
} as const

export { games };