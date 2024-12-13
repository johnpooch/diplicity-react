import { createApi, fetchBaseQuery } from "@reduxjs/toolkit/query/react";
import {
    Headers,
    Variant,
    UserConfig,
    Message,
    Game,
    PhaseState,
    Phase,
    Channel,
    User,
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
        getGame: builder.query<Game, string>({
            query: (id) => `/Game/${id}`,
            transformResponse: (response: ApiResponse<Game>) => extractProperties(response),
            providesTags: [TagType.Game],
        }),
        getRoot: builder.query<User, undefined>({
            query: () => "/",
            transformResponse: (response: ApiResponse<{ User: User }>) => extractProperties(response).User
        }),
        listVariants: builder.query<Variant[], undefined>({
            query: () => "/Variants",
            transformResponse: (response: ListApiResponse<Variant>) => extractPropertiesList(response)
        }),
        listPhases: builder.query<Phase[], string>({
            query: (gameId) => `/Game/${gameId}/Phases`,
            transformResponse: (response: ListApiResponse<Phase>) => extractPropertiesList(response)
        }),
        listGames: builder.query<Game[], ListGameFilters>({
            query: ({ my, status, mastered }) => {
                const titleStatus = status.charAt(0).toUpperCase() + status.slice(1);
                if (my) {
                    if (mastered) {
                        return `/Games/Mastered/${titleStatus}`;
                    }
                    return `/Games/My/${titleStatus}`;
                }
                return `/Games/${titleStatus}`;
            },
            transformResponse: (response: ListApiResponse<Game>) => extractPropertiesList(response),
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