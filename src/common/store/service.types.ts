type Edge = {
    Flags: {
        [key: string]: boolean;
    };
};

type Link = {
    Rel: string;
    URL: string;
    Method: string;
};

export enum GameStatus {
    Started = "started",
    Staging = "staging",
    Finished = "finished",
}

export enum NationAllocation {
    Random = "Random",
    Preference = "Preference",
}

export type Unit = {
    Type: string;
    Nation: string;
};

type Sub = {
    Name: string;
    Edges: { [key: string]: Edge };
    ReverseEdges: { [key: string]: Edge };
    Flags: {
        [key: string]: boolean;
    };
};

type Node = {
    Name: string;
    Subs: { [key: string]: Sub };
    SC: string;
};

type Graph = {
    Nodes: { [key: string]: Node };
};

type Start = {
    Year: number;
    Season: string;
    Type: string;
    SCs: { [key: string]: string };
    Units: { [key: string]: Unit };
    Map: string;
};

export type DominanceRule = {
    Priority: number;
    Nation: string;
    Dependencies: { [key: string]: string };
};

export type Variant = {
    Name: string;
    Nations: string[];
    PhaseTypes: string[];
    Season: string[];
    UnitTypes: string[];
    SvgVersion: string;
    ProvinceLongNames: { [key: string]: string };
    NationColors: null | { [key: string]: string };
    CreatedBy: string;
    Version: string;
    Description: string;
    Rules: string;
    OrderTypes: string[];
    nationAbbreviations: { [key: string]: string };
    Start: Start;
    Graph: Graph;
    Links: Link[] | null;
    ExtraDominanceRules: null | { [key: string]: DominanceRule };
};

export type TransformedVariant = {
    createdBy: string;
    description: string;
    graph: Graph;
    map: string;
    name: string;
    nationAbbreviations: { [key: string]: string };
    nationColors: null | { [key: string]: string };
    nations: string[];
    orderTypes: string[];
    phaseTypes: string[];
    provinceLongNames: { [key: string]: string };
    rules: string;
    seasons: string[];
    startSeason: string;
    startSCs: { [key: string]: string };
    startUnits: { [key: string]: Unit };
    startType: string;
    startYear: number;
    unitTypes: string[];
};

export interface ApiResponse<P> {
    Properties: P;
    Name?: string;
    Type?: string;
    Desc?: string[][];
    Links?: Link[] | null;
}

export type ListApiResponse<P> = ApiResponse<ApiResponse<P>[]>;

export type User = {
    Email: string;
    FamilyName: string;
    Gender: string;
    GivenName: string;
    Hd: string;
    Id: string;
    Link: string;
    Locale: string;
    Name: string;
    Picture: string;
    VerifiedEmail: boolean;
    ValidUntil: string;
};

export type TransformedUser = {
    id: string;
    src: string;
    username: string;
};

type TrueSkill = {
    GameID: null;
    UserId: string;
    CreatedAt: string;
    Member: string;
    Mu: number;
    Sigma: number;
    Rating: number;
    Previous: null;
    HigherRatedCount: number;
};

export type PrivateStats = {
    JoinedGames: number;
    StartedGames: number;
    FinishedGames: number;
    SoloGames: number;
    DIASGames: number;
    EliminatedGames: number;
    DroppedGames: number;
    NMRPhases: number;
    ActivePhases: number;
    ReadyPhases: number;
    Reliability: number;
    Quickness: number;
    OwnedBans: number;
    SharedBans: number;
    Hated: number;
    Hater: number;
};

export type UserStats = {
    UserId: string;
    JoinedGames: number;
    StartedGames: number;
    FinishedGames: number;
    SoloGames: number;
    DIASGames: number;
    EliminatedGames: number;
    DroppedGames: number;
    NMRPhases?: number;
    ActivePhases?: number;
    ReadyPhases?: number;
    Reliability: number;
    Quickness?: number;
    OwnedBans?: number;
    SharedBans?: number;
    Hated?: number;
    Hater?: number;
    PrivateStats?: PrivateStats;
    TrueSkill?: TrueSkill;
    User: User;
};

export type TransformedUserStats = {
    id: string;
    username: string;
    src: string;
    mu: number | undefined; // see https://trueskill.org/
    numAbandonedGames: number;
    numDrawnGames: number;
    numEliminatedGames: number;
    numFinishedGames: number;
    numJoinedGames: number;
    numNmrPhases: number | undefined;
    numSoloWinGames: number;
    numStartedGames: number;
    quickness: number | undefined;
    rating: number | undefined;
    reliability: number;
    reliabilityLabel: ReliabilityLabel;
    sigma: number | undefined; // see https://trueskill.org/
};

type FCMTokenConfig = {
    ClickActionTemplate: string;
    TitleTemplate: string;
    BodyTemplate: string;
    DontSendData: boolean;
    DontSendNotification: boolean;
};

export type Message = {
    ID: string;
    GameID: string;
    ChannelMembers: string[];
    Sender: string;
    Body: string;
    CreatedAt: string;
    Age: number;
};

export type FCMToken = {
    Value: string;
    Disabled: boolean;
    Note: string;
    App: string;
    MessageConfig: FCMTokenConfig;
    PhaseConfig: FCMTokenConfig;
    ReplaceToken: string;
};

type TemplateConfig = {
    SubjectTemplate: string;
    TextBodyTemplate: string;
    HTMLBodyTemplate: string;
};

export type ColorOverrides = {
    nationCodes: { [key: string]: string };
    variantCodes: { [key: string]: string };
    positions: string[];
    variants: { [key: string]: { [key: string]: string } };
    nations: { [key: string]: string };
};

export type UserConfig = {
    UserId?: string;
    FCMTokens?: FCMToken[] | null;
    MailConfig?: {
        Enabled?: boolean;
        UnsubscribeConfig?: {
            RedirectTemplate: string;
            HTMLTemplate: string;
        };
        MessageConfig?: {
            TextBodyTemplate: string;
        };
        PhaseConfig?: {
            TextBodyTemplate: string;
        };
    };
    MessageConfig?: TemplateConfig;
    PhaseConfig?: TemplateConfig;
    Colors?: null | string[];
    PhaseDeadlineWarningMinutesAhead?: number;
};

export type Ban = {
    UserIds: string[];
    OwnerIds: string[];
    Users: User[];
};

export type ForumMail = {
    Body?: string;
    Secret?: string;
    Subject?: string;
};

export type UserRatingHistogram = {
    FirstBucketRating: number;
    Counts: number[];
};

export enum Headers {
    Authorization = "authorization",
    Accept = "Accept",
    ContentType = "content-type",
    XDiplicityAPILevel = "X-Diplicity-API-Level",
    XDiplicityClientName = "X-Diplicity-Client-Name",
}

export type NewGame = {
    Anonymous: boolean;
    ChatLanguageISO639_1: string;
    Desc: string;
    DisableConferenceChat: boolean;
    DisableGroupChat: boolean;
    DisablePrivateChat: boolean;
    FirstMember?: Pick<Member, "NationPreferences">;
    GameMasterEnabled: boolean;
    LastYear: number;
    MaxHated: number | null;
    MaxHater: number;
    MaxRating: number;
    MinQuickness: number;
    MinRating: number;
    MinReliability: number;
    NationAllocation: number;
    NonMovementPhaseLengthMinutes: number;
    PhaseLengthMinutes: number;
    Private: boolean;
    RequireGameMasterInvitation: boolean;
    SkipMuster: boolean;
    Variant: string;
};

export type PhaseState = {
    GameID: string;
    PhaseOrdinal: number;
    Nation: string;
    ReadyToResolve: boolean;
    WantsDIAS: boolean;
    WantsConcede: boolean;
    OnProbation: boolean;
    NoOrders: boolean;
    Eliminated: boolean;
    Messages: string;
    ZippedOptions: null;
    Note: string;
};

export type Member = {
    User: User;
    Nation: string;
    GameAlias: string;
    NationPreferences: string;
    UnreadMessages: number;
    Replacable: boolean;
    NewestPhaseState: PhaseState;
};

export interface PhaseMeta {
    PhaseOrdinal: number;
    Season: string;
    Year: number;
    Type: string;
    Resolved: false;
    CreatedAt: string;
    CreatedAgo: number;
    ResolvedAt: string;
    ResolvedAgo: number;
    DeadlineAt: string;
    NextDeadlineIn: number;
    UnitsJSON: string;
    SCsJSON: string;
}

export type GameMasterInvitation = {
    Email: string;
    Nation: string;
};

export type Game = Omit<NewGame, "FirstMember"> & {
    ActiveBans: null;
    Closed: boolean;
    CreatedAgo: number;
    CreatedAt: string;
    FailedRequirements: null | string[];
    Finished: boolean;
    FinishedAgo: number;
    FinishedAt: string;
    FirstMember: Member;
    GameMaster: User;
    GameMasterInvitations: null | GameMasterInvitation[];
    ID: string;
    Members: Member[];
    Mustered: boolean;
    NMembers: number;
    NewestPhaseMeta: PhaseMeta[] | null;
    NoMerge: boolean;
    StartETA: string;
    Started: boolean;
    StartedAgo: number;
    StartedAt: string;
};

export type TransformedGamePlayer = {
    id: string;
    username: string;
    src: string;
    nation?: string;
};

export type TransformedGame = {
    anonymous: boolean;
    chatDisabled: boolean;
    chatLanguage: string;
    chatLanguageDisplay: string;
    closed: boolean;
    conferenceChatEnabled: boolean;
    confirmationStatus: "confirmed" | "notConfirmed" | "nmr" | undefined;
    createdAt: string;
    deadline: string;
    endYear: number;
    finished: boolean;
    finishedAt: string;
    gameMaster: TransformedGamePlayer | undefined;
    groupChatEnabled: boolean;
    id: string;
    name: string;
    nationAllocation: NationAllocation;
    newestPhaseMeta: PhaseMeta[] | null;
    nonMovementPhaseLength: string;
    numPlayers: number;
    phaseLength: string;
    phaseSummary: string;
    playerIdentity: "anonymous" | "public";
    players: TransformedGamePlayer[];
    privateChatEnabled: boolean;
    privateGame: boolean;
    rulesSummary: string;
    started: boolean;
    startedAt: string;
    status: "staging" | "started" | "finished";
    userIsPlayer: (user: TransformedUser) => boolean;
    userIsGameMaster: (user: TransformedUser) => boolean;
    variant: string;
    visibility: "private" | "public";
};

export interface Player {
    id: string;
    username: string;
    image: string;
}

export type GameState = {
    GameID: string;
    Nation: string;
    Muted: null | string[];
};

export type UnitState = {
    Province: string;
    Unit: Unit;
};

export type SCState = {
    Province: string;
    Owner: string;
};

export type Resolution = {
    Province: string;
    Resolution: string;
};

export type PreliminaryScore = {
    UserId: string;
    Member: string;
    SCs: number;
    Score: number;
    Explanation: string;
};

export type Bounce = {
    Province: string;
    BounceList: string;
};

export type Dislodged = {
    Province: string;
    Dislodged: Unit;
};

export type Dislodger = {
    Province: string;
    Dislodger: string;
};

export type Phase = {
    PhaseOrdinal: number;
    Season: string;
    Year: number;
    Type: string;
    Resolved: boolean;
    CreatedAt: string;
    CreatedAgo: number;
    ResolvedAt: string;
    ResolvedAgo: number;
    DeadlineAt: string;
    NextDeadlineIn: number;
    UnitsJSON: string;
    SCsJSON: string;
    GameID: string;
    Units: UnitState[];
    SCs: SCState[];
    Dislodgeds: null | Dislodged[];
    Dislodgers: null | Dislodger[];
    ForceDisbands: null | string[];
    Bounces: null | Bounce[];
    Resolutions: null | Resolution[];
    Host: string;
    SoloSCCount: number;
    PreliminaryScores: PreliminaryScore[];
};

export type TransformedUnit = {
    type: string;
    nation: string;
};

export type TransformedUnitState = {
    province: string;
    unit: TransformedUnit;
};
export type TransformedSupplyCenterState = {
    province: string;
    owner: string;
};
export type TransformedDislodgedUnit = {
    province: string;
    unit: TransformedUnit;
};
export type TransformedDislodgingProvinces = {
    province: string;
    dislodgingProvince: string;
};

export type TransformedPhase = {
    id: number;
    season: string;
    year: number;
    type: string;
    resolved: boolean;
    createdAt: string;
    resolvedAt: string;
    deadlineAt: string;
    units: TransformedUnitState[];
    supplyCenters: TransformedSupplyCenterState[];
    dislodgedUnits: TransformedDislodgedUnit[];
    dislodgingProvinces: TransformedDislodgingProvinces[];
};

export type HasPermissionType = "unknown" | "true" | "false";
export type TargetStateType = "undefined" | "enabled" | "disabled";

export type Messaging = {
    hasPermission: HasPermissionType;
    hasToken: boolean;
    globalToken?: FCMToken;
    targetState: TargetStateType;
    token: string | null;
    tokenApp: string;
    tokenEnabled: boolean;
    tokenOnServer: boolean;
};

export interface ColorMap {
    [key: string]: {
        name: string;
        color: string;
        edited: boolean;
    }[];
}

export interface SettingsFormValues {
    colors: { [key: string]: { [key: string]: string } };
    enablePushNotifications: boolean;
    enableEmailNotifications: boolean;
    enableColorNonSCs: boolean;
    phaseDeadline: number;
}

export type Channel = {
    GameID: string;
    Members: string[];
    NMessages: number;
    LatestMessage: Message;
    NMessagesSince?: {
        Since: string;
        NMessages: number;
    };
};

export interface MutationStatus {
    isLoading: boolean;
    isError: boolean;
    isSuccess: boolean;
}

export type Order = {
    GameID: string;
    PhaseOrdinal: number;
    Nation: string;
    Parts: string[];
};

export type Corroboration = {
    Orders: Order[] | null;
    Inconsistencies: string[];
};

export interface CreateGameFormValues {
    adjustmentPhaseLengthMultiplier: number;
    adjustmentPhaseLengthUnit: number;
    anonymousEnabled: boolean;
    chatLanguage: string;
    conferenceChatEnabled: boolean;
    customAdjustmentPhaseLength: boolean;
    endAfterYears: boolean;
    endAfterYearsValue: number;
    gameMaster: boolean;
    groupChatEnabled: boolean;
    individualChatEnabled: boolean;
    maxRating: number;
    maxRatingEnabled: boolean;
    minQuickness: number;
    minRating: number;
    minRatingEnabled: boolean;
    minReliability: number;
    name: string;
    nationAllocation: string;
    phaseLengthMultiplier: number;
    phaseLengthUnit: number;
    privateGame: boolean;
    quicknessEnabled: boolean;
    reliabilityEnabled: boolean;
    requireGameMasterInvitation: boolean;
    skipGetReadyPhase: boolean;
    variant: string;
}

export type DiplicityError = {
    status: number;
};

export interface Query<T> {
    isError: boolean;
    isLoading: boolean;
    isFetching?: boolean;
    isSuccess: boolean;
    data?: T | null;
}

export type PhasesDisplay = [number, string][];

export interface NationDisplay {
    abbreviation: string;
    color: string;
    flagLink: string;
    name: string;
    isUser: boolean;
}

export type ResolutionDisplay = {
    message: string;
    province?: string;
};

export interface OrderDisplay {
    label: string;
    inconsistencies: string[];
    resolution: ResolutionDisplay | null;
}

export interface NationStatusDisplay {
    confirmedOrders: boolean;
    noOrdersGiven: boolean;
    numBuilds: number | null;
    numDisbands: number | null;
    numSupplyCenters: number;
    numSupplyCentersToWin: number;
    wantsDraw: boolean;
    nation: NationDisplay;
    orders: OrderDisplay[];
    homelessInconsistencies: string[];
}

export enum UnitType {
    Fleet,
    Army,
}

export enum OrderType {
    Buid = "Build",
    Convoy = "Convoy",
    Disband = "Disband",
    Hold = "Hold",
    Move = "Move",
    MoveViaConvoy = "MoveViaConvoy",
    Support = "Support",
}

export enum OrderMenuOption {
    Hold,
    Move,
    MoveViaConvoy,
    Convoy,
    Support,
    Clear,
    Cancel,
}

export enum CreateOrderStep {
    SelectSource,
    SelectType,
    SelectTarget,
    SelectAux,
    SelectAuxTarget,
    Complete,
}

export interface CreateOrder {
    source?: string;
    type?: OrderType;
    target?: string;
    aux?: string;
}

export interface UnitDisplay {
    type: UnitType;
    color: string;
}

export interface ProvinceDisplay {
    name: string;
    id: string;
    color: string;
    unit: UnitDisplay | null;
    dislodgedUnit: UnitDisplay | null;
    highlight: boolean;
}

export interface Option {
    Next: { [key: string]: Option };
    Type: string;
}

export interface Options {
    [key: string]: Option;
}

// TODO select MapState TDD
export interface MapState {
    provinces: {
        id: string;
        fill: string;
        highlight: boolean;
    }[];
    units: {
        fill: string;
        province: string;
        type: string;
    }[];
    orders: {
        type: string;
        source: string;
        target: string;
        aux: string;
        fill: string;
        result: string;
    }[];
}

export type ReliabilityLabel = "commited" | "uncommited" | "disengaged";

export interface PlayerDisplay {
    id: string;
    username: string;
    src?: string;
    stats: {
        reliabilityLabel: ReliabilityLabel;
        reliabilityRating: number;
        numPlayedGames: number;
        numWonGames: number;
        numDrawnGames: number;
        numAbandonedGames: number;
    };
}

export type GameDetailViewActions = "join" | "leave";

export type ChatMode = "all" | "disabled";