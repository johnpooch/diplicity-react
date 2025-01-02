import { z } from "zod";
import { apiResponseSchema, listApiResponseSchema } from "./common";

const transformMinutesToDisplayString = (minutes: number) => {
    if (minutes === 0) {
        return undefined;
    }
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    if (hours > 0 && remainingMinutes > 0) {
        return `${hours} hours ${remainingMinutes} minutes`;
    }
    if (hours > 0) {
        return `${hours} hours`;
    }
    return `${remainingMinutes} minutes`;
}

const phaseMetaSchema = z.object({
    PhaseOrdinal: z.number(),
    Season: z.string(),
    Year: z.number(),
    Type: z.string(),
    Resolved: z.boolean(),
    CreatedAt: z.string(),
    CreatedAgo: z.number(),
    ResolvedAt: z.string(),
    ResolvedAgo: z.number(),
    DeadlineAt: z.string(),
    NextDeadlineIn: z.number().transform((val) => transformMinutesToDisplayString(Math.floor(val / 1000000000 / 60))),
    UnitsJSON: z.string(),
    SCsJSON: z.string(),
});

const transformReliabilityToDisplayString = (reliability: number) => {
    if (reliability === 0) {
        return undefined
    };
    return "Commited";
}

const transformRatingToDisplayString = (rating: number) => {
    if (rating === 0) {
        return undefined
    };
    return "Private first class";
}

const userSchema = z.object({
    Email: z.string(),
    FamilyName: z.string(),
    Gender: z.string(),
    GivenName: z.string(),
    Hd: z.string(),
    Id: z.string(),
    Locale: z.string(),
    Name: z.string(),
    Picture: z.string().url(),
    VerifiedEmail: z.boolean(),
    ValidUntil: z.string(),
});

const phaseStateSchema = z.object({
    GameID: z.string().nullable(),
    PhaseOrdinal: z.number(),
    Nation: z.string(),
    ReadyToResolve: z.boolean(),
    WantsDIAS: z.boolean(),
    WantsConcede: z.boolean(),
    OnProbation: z.boolean(),
    NoOrders: z.boolean(),
    Eliminated: z.boolean(),
    Messages: z.string(),
    ZippedOptions: z.string().nullable(),
    Note: z.string(),
});

const memberSchema = z.object({
    User: userSchema,
    Nation: z.string(),
    GameAlias: z.string(),
    NationPreferences: z.string(),
    UnreadMessages: z.number(),
    Replaceable: z.boolean(),
    NewestPhaseState: phaseStateSchema,
});

const gameSchema = z.object({
    Anonymous: z.boolean(),
    ChatLanguageISO639_1: z.string(),
    Desc: z.string(),
    DisableConferenceChat: z.boolean(),
    DisableGroupChat: z.boolean(),
    DisablePrivateChat: z.boolean(),
    Finished: z.boolean(),
    GameMasterEnabled: z.boolean(),
    ID: z.string(),
    LastYear: z.number(),
    MaxHated: z.number().nullable(),
    MaxHater: z.number(),
    MaxRating: z.number().transform(transformRatingToDisplayString),
    Members: z.array(memberSchema),
    MinQuickness: z.number(),
    MinRating: z.number().transform(transformRatingToDisplayString),
    MinReliability: z.number().transform(transformReliabilityToDisplayString),
    NMembers: z.number(),
    NationAllocation: z.number(),
    NonMovementPhaseLengthMinutes: z.number().transform(transformMinutesToDisplayString),
    PhaseLengthMinutes: z.number().transform(transformMinutesToDisplayString),
    Private: z.boolean(),
    RequireGameMasterInvitation: z.boolean(),
    SkipMuster: z.boolean(),
    Started: z.boolean(),
    Variant: z.string(),
    ActiveBans: z.array(z.object({
        UserId: z.string(),
        GameId: z.string(),
        Reason: z.string(),
        BannedBy: z.string(),
        BannedAt: z.string(),
    })).nullable(),
    Closed: z.boolean(),
    NewestPhaseMeta: z.nullable(z.array(phaseMetaSchema).min(1).max(1)).transform((val) => val?.[0]),
});

// Create the listGamesSchema
const listGamesSchema = listApiResponseSchema(apiResponseSchema(gameSchema)).transform((data) => {
    const transformLinks = (links: ReturnType<ReturnType<typeof apiResponseSchema>["parse"]>["Links"]) => {
        const canJoin = links.some(link => link.Rel === "join");
        const canLeave = links.some(link => link.Rel === "leave");
        return { canJoin, canLeave };
    };

    const transformedProperties = data.Properties.map((response) => {
        const { canJoin, canLeave } = transformLinks(response.Links);
        const game = response.Properties;
        const status = game.Finished ? "finished" : game.Started ? "started" : "staging";
        const transformedGame = { ...game, canJoin, canLeave, status };
        return { ...response, Properties: transformedGame };
    });

    return { ...data, Properties: transformedProperties };
});

export { gameSchema, listGamesSchema };