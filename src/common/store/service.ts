import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import {
    Headers,
    UserConfig,
    Message,
    Game,
    PhaseState,
    Channel,
    Member,
    GameMasterInvitation,
    UserStats,
    GameState,
    Ban,
    UserRatingHistogram,
    Corroboration,
    Options,
    ApiResponse,
    ForumMail,
    ListApiResponse,
    CreateGameFormValues,
} from "./service.types";
import { selectAuth } from "./auth";
import { z } from "zod";

const apiResponseSchema = <TObjSchema extends z.ZodRawShape>(schema: z.ZodObject<TObjSchema>) => z.object({
    Properties: schema,
    Links: z.array(z.object({
        Rel: z.string(),
        URL: z.string(),
        Method: z.string(),
    })),
})
const listApiResponseSchema = <TObjSchema extends z.ZodRawShape>(schema: z.ZodObject<TObjSchema>) => z.object({
    Properties: z.array(apiResponseSchema(schema)),
})

enum TagType {
    Game = "Game",
    ListGames = "ListGames",
    Messages = "Messages",
    PhaseState = "PhaseState",
    Token = "Token",
    UserConfig = "UserConfig",
}

type ListGameFilters = {
    my: boolean;
    status: string;
    mastered: boolean;
}

const extractProperties = <T>(response: ApiResponse<T>) =>
    response.Properties;

const extractPropertiesList = <T>(response: ListApiResponse<T>) => {
    return response.Properties.map((response) => response.Properties);
};

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

const variantSchema = z.object({
    Name: z.string(),
    Nations: z.array(z.string()),
    PhaseTypes: z.array(z.string()),
    Seasons: z.array(z.string()),
    UnitTypes: z.array(z.string()),
    SvgVersion: z.string().optional(),
    ProvinceLongNames: z.record(z.string()).nullable(),
    NationColors: z.record(z.string()).nullable(),
    CreatedBy: z.string(),
    Version: z.string(),
    Description: z.string(),
    Rules: z.string(),
    OrderTypes: z.array(z.string()),
    Start: z.object({
        Year: z.number(),
        Season: z.string(),
        Type: z.string(),
        SCs: z.record(z.string()),
        Units: z.record(z.object({
            Type: z.string(),
            Nation: z.string(),
        })),
        Map: z.string(),
    }),
    Graph: z.object({
        Nodes: z.record(z.object({
            Name: z.string(),
            Subs: z.record(z.object({
                Name: z.string(),
                Edges: z.record(z.object({
                    Flags: z.record(z.boolean()),
                })),
                ReverseEdges: z.record(z.object({
                    Flags: z.record(z.boolean()),
                })),
                Flags: z.record(z.boolean()),
            })),
            SC: z.optional(z.string().nullable()),
        })),
    }),
    ExtraDominanceRules: z.record(z.object({
        Priority: z.number(),
        Nation: z.string(),
        Dependencies: z.record(z.string()),
    })).nullable(),
})

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
    NextDeadlineIn: z.number(),
    UnitsJSON: z.string(),
    SCsJSON: z.string(),
});

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
    NewestPhaseMeta: z.nullable(z.array(phaseMetaSchema).min(1).max(1)),
});

const rootSchema = z.object({
    User: userSchema,
})

const unitSchema = z.object({
    Type: z.string(),
    Nation: z.string(),
});

const unitStateSchema = z.object({
    Province: z.string(),
    Unit: unitSchema,
});

const scStateSchema = z.object({
    Province: z.string(),
    Owner: z.string(),
});

const dislodgedSchema = z.object({
    Province: z.string(),
    Dislodged: unitSchema,
});

const dislodgerSchema = z.object({
    Province: z.string(),
    Dislodger: z.string(),
});

const bounceSchema = z.object({
    Province: z.string(),
    BounceList: z.string(),
});

const resolutionSchema = z.object({
    Province: z.string(),
    Resolution: z.string(),
});

const phaseSchema = z.object({
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
    NextDeadlineIn: z.number(),
    UnitsJSON: z.string(),
    SCsJSON: z.string(),
    GameID: z.string(),
    Units: z.array(unitStateSchema),
    SCs: z.array(scStateSchema),
    Dislodgeds: z.array(dislodgedSchema).nullable(),
    Dislodgers: z.array(dislodgerSchema).nullable(),
    ForceDisbands: z.array(z.string()).nullable(),
    Bounces: z.array(bounceSchema).nullable(),
    Resolutions: z.array(resolutionSchema).nullable(),
    Host: z.string(),
    SoloSCCount: z.number(),
    PreliminaryScores: z.array(
        z.object({
            UserId: z.string(),
            Member: z.string(),
            SCs: z.number(),
            Score: z.number(),
            Explanation: z.string(),
        })
    ),
});

const baseUrl = "https://diplicity-engine.appspot.com/";

export default createApi({
    tagTypes: [
        TagType.Game,
        TagType.ListGames,
        TagType.Messages,
        TagType.PhaseState,
        TagType.Token,
        TagType.UserConfig,
    ],
    reducerPath: "service",
    baseQuery: fetchBaseQuery({
        baseUrl,
        prepareHeaders: async (headers, { getState }) => {
            const token = selectAuth(getState() as Parameters<typeof selectAuth>[0]).token;
            if (token) {
                headers.set(Headers.Authorization, `Bearer ${token}`);
            }
            headers.set(Headers.XDiplicityAPILevel, "8");
            headers.set(Headers.XDiplicityClientName, "dipact@"); // TODO
            headers.set(Headers.Accept, "application/json");
            headers.set(Headers.ContentType, "application/json");
            return headers;
        },
        mode: "cors",
    }),
    endpoints: (builder) => ({
        getVariantSVG: builder.query<string, string>({
            query: (variantName) => ({
                url: `/Variant/${variantName}/Map.svg`,
                responseHandler: (response) => response.text(),
            }),
        }),
        getVariantUnitSVG: builder.query<
            string,
            { variantName: string; unitType: string }
        >({
            query: ({ variantName, unitType }) => ({
                url: `/Variant/${variantName}/Units/${unitType}.svg`,
                responseHandler: (response) => response.text(),
            }),
        }),
        getVariantFlagSVG: builder.query<string, { variantName: string; nationName: string }>({
            query: ({ variantName, nationName }) => ({
                url: `/Variant/${variantName}/Flags/${nationName}.svg`,
                responseHandler: (response) => response.text(),
            }),
        }),
        getForumMail: builder.query<ApiResponse<ForumMail>, undefined>({
            query: () => "/ForumMail",
        }),
        listUserBans: builder.query<Ban[], string>({
            query: (id) => `/User/${id}/Bans`,
            transformResponse: extractPropertiesList,
        }),
        getUserConfig: builder.query<UserConfig, string>({
            query: (id) => `/User/${id}/UserConfig`,
            transformResponse: extractProperties,
            providesTags: [TagType.UserConfig],
        }),
        getUserRatingHistogram: builder.query<UserRatingHistogram, undefined>({
            query: () => "/Users/Ratings/Histogram",
            transformResponse: extractProperties,
        }),
        // TODO test
        listMessages: builder.query<
            Message[],
            { gameId: string; channelId: string }
        >({
            query: ({ gameId, channelId }) =>
                `/Game/${gameId}/Channel/${channelId}/Messages`,
            transformResponse: (response: ListApiResponse<Message>) => extractPropertiesList(response),
            providesTags: [TagType.Messages],
        }),
        listPhaseStates: builder.query<
            PhaseState[],
            { gameId: string; phaseId: string }
        >({
            query: ({ gameId, phaseId }) =>
                `/Game/${gameId}/Phase/${phaseId}/PhaseStates`,
            transformResponse: extractPropertiesList,
            providesTags: [TagType.PhaseState],
        }),
        getGameState: builder.query<
            GameState,
            { gameId: string; userId: string }
        >({
            query: ({ gameId, userId }) => `/Game/${gameId}/GameStates/${userId}`,
            transformResponse: extractProperties,
            providesTags: [TagType.ListGames],
        }),
        listGameStates: builder.query<GameState[], string>({
            query: (gameId) => `/Game/${gameId}/GameStates`,
            transformResponse: extractPropertiesList,
            providesTags: [TagType.ListGames],
        }),
        listChannels: builder.query<Channel[], string>({
            query: (gameId) => `/Game/${gameId}/Channels`,
            transformResponse: (response: ListApiResponse<Channel>) => extractPropertiesList(response)
        }),
        listOrders: builder.query<
            Corroboration,
            { gameId: string; phaseId: string }
        >({
            query: ({ gameId, phaseId }) =>
                `/Game/${gameId}/Phase/${phaseId}/Corroborate`,
            transformResponse: extractProperties,
        }),
        listOptions: builder.query<Options, { gameId: string; phaseId: string }>({
            query: ({ gameId, phaseId }) =>
                `/Game/${gameId}/Phase/${phaseId}/Options`,
            transformResponse: extractProperties,
        }),
        createOrder: builder.mutation<
            ApiResponse<Corroboration>,
            { Parts: string[]; gameId: string; phaseId: string }
        >({
            query: ({ gameId, phaseId, ...data }) => ({
                url: `/Game/${gameId}/Phase/${phaseId}/CreateAndCorroborate`,
                method: "POST",
                body: data,
            }),
        }),
        createMessage: builder.mutation<
            Message,
            Pick<Message, "Body" | "ChannelMembers"> & { gameId: string }
        >({
            query: ({ gameId, ...data }) => ({
                url: `/Game/${gameId}/Messages`,
                method: "POST",
                body: JSON.stringify(data),
            }),
            transformResponse: extractProperties,
            invalidatesTags: [TagType.Messages],
        }),
        updateUserConfig: builder.mutation<
            ApiResponse<UserConfig>,
            Partial<UserConfig> & Pick<UserConfig, "UserId">
        >({
            query: ({ UserId, ...patch }) => ({
                url: `/User/${UserId}/UserConfig`,
                method: "PUT",
                body: { UserId, ...patch },
            }),
            invalidatesTags: [TagType.UserConfig],
        }),
        updatePhaseState: builder.mutation<
            ApiResponse<PhaseState>,
            Partial<PhaseState> &
            Pick<PhaseState, "GameID"> &
            Pick<PhaseState, "PhaseOrdinal">
        >({
            query: ({ GameID, PhaseOrdinal, ...patch }) => {
                return {
                    url: `/Game/${GameID}/Phase/${PhaseOrdinal}/PhaseState`,
                    method: "PUT",
                    body: { GameID, PhaseOrdinal, ...patch },
                };
            },
            invalidatesTags: [TagType.Game, TagType.PhaseState],
        }),
        joinGame: builder.mutation<
            undefined,
            Pick<Member, "NationPreferences" | "GameAlias"> & { gameId: string }
        >({
            query: ({ gameId, ...data }) => ({
                url: `/Game/${gameId}/Member`,
                method: "POST",
                body: JSON.stringify(data),
            }),
            invalidatesTags: [TagType.ListGames],
        }),
        rescheduleGame: builder.mutation<
            undefined,
            {
                gameId: string;
                PhaseOrdinal: number;
                NextPhaseDeadlineInMinutes: number;
            }
        >({
            query: ({ gameId, PhaseOrdinal, ...data }) => ({
                url: `/Game/${gameId}/Phase/${PhaseOrdinal}/DeadlineAt`,
                method: "POST",
                body: JSON.stringify(data),
            }),
            invalidatesTags: [TagType.ListGames],
        }),
        unInvite: builder.mutation<undefined, { gameId: string; email: string }>({
            query: ({ gameId, email }) => ({
                url: `/Game/${gameId}/${email}`,
                method: "DELETE",
            }),
            invalidatesTags: [TagType.ListGames],
        }),
        invite: builder.mutation<
            undefined,
            GameMasterInvitation & { gameId: string }
        >({
            query: ({ gameId, ...data }) => ({
                url: `/Game/${gameId}`,
                method: "POST",
                body: JSON.stringify(data),
            }),
            invalidatesTags: [TagType.ListGames],
        }),
        renameGame: builder.mutation<
            undefined,
            { gameId: string; userId: string; GameAlias: string }
        >({
            query: ({ gameId, userId, ...data }) => ({
                url: `/Game/${gameId}/Member/${userId}`,
                method: "PUT",
                body: JSON.stringify(data),
            }),
            invalidatesTags: [TagType.ListGames],
        }),
        deleteGame: builder.mutation<undefined, string>({
            query: (gameId) => ({
                url: `/Game/${gameId}`,
                method: "DELETE",
            }),
            invalidatesTags: [TagType.ListGames],
        }),
        getGame: builder.query({
            query: (id) => `/Game/${id}`,
            transformResponse: (response) => {
                const parsed = apiResponseSchema(gameSchema).parse(response);
                const extracted = extractProperties(parsed);
                return {
                    ...extracted,
                    Links: parsed.Links,
                };
            },
            providesTags: [TagType.Game],
        }),
        getRoot: builder.query({
            query: () => "/",
            // transformResponse: (response) => extractProperties(response).User
            transformResponse: (response) => {
                const parsed = apiResponseSchema(rootSchema).parse(response);
                return extractProperties(parsed).User;
            }
        }),
        listVariants: builder.query({
            query: () => "/Variants",
            transformResponse: (response) => {
                const parsed = listApiResponseSchema(variantSchema).parse(response);
                return extractPropertiesList(parsed);
            }
        }),
        listPhases: builder.query({
            query: (gameId) => `/Game/${gameId}/Phases`,
            transformResponse: (response) => {
                const parsed = listApiResponseSchema(phaseSchema).parse(response);
                return extractPropertiesList(parsed);
            }
        }),
        listGames: builder.query({
            query: ({ my, status, mastered }: ListGameFilters) => {
                const titleStatus = status.charAt(0).toUpperCase() + status.slice(1);
                if (my) {
                    if (mastered) {
                        return `/Games/Mastered/${titleStatus}`;
                    }
                    return `/Games/My/${titleStatus}`;
                }
                return `/Games/${titleStatus}`;
            },
            transformResponse: (response) => {
                const parsed = listApiResponseSchema(gameSchema).parse(response);
                const extracted = extractPropertiesList(parsed);
                return extracted.map((game, index) => ({
                    ...game,
                    Links: parsed.Properties[index].Links,
                }));
            },
            providesTags: [TagType.ListGames],
        }),
        getUserStats: builder.query<UserStats, string>({
            query: (id) => `/User/${id}/Stats`,
            transformResponse: (response: ApiResponse<UserStats>) => extractProperties(response),
        }),
        createGame: builder.mutation<Game, CreateGameFormValues>({
            query: (data) => {
                return {
                    url: "/Game",
                    method: "POST",
                    body: data
                };
            },
            transformResponse: (response: ApiResponse<Game>) => extractProperties(response),
        }),
    })
});

type Phase = z.infer<typeof phaseSchema>;
type Variant = z.infer<typeof variantSchema>;

export type { Phase, Variant }

