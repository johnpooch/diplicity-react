import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import {
    Headers,
    UserConfig,
    Message,
    PhaseState,
    Member,
    GameMasterInvitation,
    UserStats,
    GameState,
    Ban,
    UserRatingHistogram,
    Corroboration,
    ApiResponse,
    ForumMail,
    ListApiResponse,
} from "./service.types";
import { selectAuth } from "./auth";
import { z } from "zod";
import { gameSchema, getGameSchema, listGamesSchema, listOrdersSchema, listPhasesSchema, listPhaseStatesSchema, listMessagesSchema, listChannelsSchema, createMessageSchema, listVariantsSchema, listOptionsSchema } from "../schema";

const apiResponseSchema = <TObjSchema extends z.ZodRawShape>(schema: z.ZodObject<TObjSchema>) => z.object({
    Properties: schema,
    Links: z.array(z.object({
        Rel: z.string(),
        URL: z.string(),
        Method: z.string(),
    })),
}).transform((val) => (
    { ...val, Properties: { ...val.Properties, Links: val.Links } }
));

const listApiResponseSchema = <TObjSchema extends z.ZodRawShape>(schema: z.ZodObject<TObjSchema>) => z.object({
    Properties: z.array(apiResponseSchema(schema)),
})

enum TagType {
    Game = "Game",
    ListGames = "ListGames",
    Channels = "Channels",
    Messages = "Messages",
    PhaseState = "PhaseState",
    Token = "Token",
    UserConfig = "UserConfig",
    Orders = "Orders",
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

const rootSchema = z.object({
    User: userSchema,
})

const newGameSchema = z.object({
    Anonymous: z.boolean(),
    ChatLanguageISO639_1: z.string().optional(),
    Desc: z.string(),
    DisableConferenceChat: z.boolean(),
    DisableGroupChat: z.boolean(),
    DisablePrivateChat: z.boolean(),
    FirstMember: z.object({
        NationPreferences: z.string().optional(),
    }).optional(),
    GameMasterEnabled: z.boolean(),
    LastYear: z.number(),
    MaxHated: z.number().nullable(),
    MaxHater: z.number(),
    MaxRating: z.number(),
    MinQuickness: z.number(),
    MinRating: z.number(),
    MinReliability: z.number(),
    NationAllocation: z.number(),
    NonMovementPhaseLengthMinutes: z.number(),
    PhaseLengthMinutes: z.number(),
    Private: z.boolean(),
    RequireGameMasterInvitation: z.boolean(),
    SkipMuster: z.boolean(),
    Variant: z.string(),
});

const baseUrl = "https://diplicity-engine.appspot.com/";

const service = createApi({
    tagTypes: [
        TagType.Game,
        TagType.ListGames,
        TagType.Channels,
        TagType.Messages,
        TagType.PhaseState,
        TagType.Token,
        TagType.UserConfig,
        TagType.Orders,
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
        getVariantSvg: builder.query<string, string>({
            query: (variantName) => ({
                url: `/Variant/${variantName}/Map.svg`,
                responseHandler: (response) => response.text(),
            }),
        }),
        getVariantUnitSvg: builder.query<
            string,
            { variantName: string; unitType: string }
        >({
            query: ({ variantName, unitType }) => ({
                url: `/Variant/${variantName}/Units/${unitType}.svg`,
                responseHandler: (response) => response.text(),
            }),
        }),
        getVariantFlagSvg: builder.query<string, { variantName: string; nationName: string }>({
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
        listMessages: builder.query({
            query: ({ gameId, channelId }) =>
                `/Game/${gameId}/Channel/${channelId}/Messages`,
            transformResponse: (response) => {
                const parsed = listMessagesSchema.parse(response);
                return extractPropertiesList(parsed);
            },
            providesTags: [TagType.Messages],
        }),
        listPhaseStates: builder.query({
            query: ({ gameId, phaseId }) =>
                `/Game/${gameId}/Phase/${phaseId}/PhaseStates`,
            transformResponse: (response) => {
                const parsed = listPhaseStatesSchema.parse(response);
                return extractPropertiesList(parsed);
            },
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
        listChannels: builder.query({
            query: (gameId) => `/Game/${gameId}/Channels`,
            transformResponse: (response) => {
                const parsed = listChannelsSchema.parse(response);
                return extractPropertiesList(parsed);
            },
            providesTags: [TagType.Channels],
        }),
        listOrders: builder.query({
            query: ({ gameId, phaseId }) =>
                `/Game/${gameId}/Phase/${phaseId}/Corroborate`,
            transformResponse: (response) => {
                const parsed = listOrdersSchema.parse(response);
                return extractProperties(parsed);
            },
            providesTags: [TagType.Orders]
        }),
        listOptions: builder.query({
            query: ({ gameId, phaseId }) =>
                `/Game/${gameId}/Phase/${phaseId}/Options`,
            transformResponse: (response) => {
                const parsed = listOptionsSchema.parse(response);
                return extractProperties(parsed);
            }
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
            invalidatesTags: [TagType.Orders],
        }),
        createMessage: builder.mutation({
            query: ({ gameId, ...data }: Pick<Message, "Body" | "ChannelMembers"> & { gameId: string }) => ({
                url: `/Game/${gameId}/Messages`,
                method: "POST",
                body: JSON.stringify(data),
            }),
            transformResponse: (response) => {
                const parsed = createMessageSchema.parse(response);
                return extractProperties(parsed);
            },
            invalidatesTags: [TagType.Messages, TagType.Channels],
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
            invalidatesTags: [TagType.ListGames, TagType.Game],
        }),
        leaveGame: builder.mutation({
            query: ({ gameId, userId }) => ({
                url: `/Game/${gameId}/Member/${userId}`,
                method: "DELETE",
            }),
            invalidatesTags: [TagType.ListGames, TagType.Game],
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
                const parsed = getGameSchema.parse(response);
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
                const parsed = listVariantsSchema.parse(response);
                return extractPropertiesList(parsed);
            }
        }),
        listPhases: builder.query({
            query: (gameId) => `/Game/${gameId}/Phases`,
            transformResponse: (response) => {
                const parsed = listPhasesSchema.parse(response);
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
                const parsed = listGamesSchema.parse(response);
                return extractPropertiesList(parsed);
            },
            providesTags: [TagType.ListGames],
        }),
        getUserStats: builder.query<UserStats, string>({
            query: (id) => `/User/${id}/Stats`,
            transformResponse: (response: ApiResponse<UserStats>) => extractProperties(response),
        }),
        createGame: builder.mutation({
            query: (data: z.infer<typeof newGameSchema>) => {
                const parsed = newGameSchema.parse(data);
                return {
                    url: "/Game",
                    method: "POST",
                    body: parsed
                };
            },
            transformResponse: (response) => {
                const parsed = apiResponseSchema(gameSchema).parse(response);
                return extractProperties(parsed);
            }
        }),
    })
});

export { newGameSchema, gameSchema, apiResponseSchema, extractProperties, extractPropertiesList, listApiResponseSchema, service }

export default service;
