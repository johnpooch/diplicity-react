import { createSelector } from "@reduxjs/toolkit";
import service from "./service";
import { createGameDisplay } from "../display";

const selectRootQuery = createSelector(
    service.endpoints.getRoot.select(undefined),
    (result) => result
)

const selectListVariantsQuery = createSelector(
    service.endpoints.listVariants.select(undefined),
    (result) => result
)

const selectListMyStagingGamesQuery = createSelector(
    service.endpoints.listGames.select({
        my: true,
        status: "Staging",
        mastered: false,
    }),
    (result) => result
)

const selectListMyStartedGamesQuery = createSelector(
    service.endpoints.listGames.select({
        my: true,
        status: "Started",
        mastered: false,
    }),
    (result) => result
)

const selectListMyFinishedGamesQuery = createSelector(
    service.endpoints.listGames.select({
        my: true,
        status: "Finished",
        mastered: false,
    }),
    (result) => result
)

type HomeScreenView = {
    isLoading: boolean;
    isSuccess: boolean;
    data?: {
        stagingGames: ReturnType<typeof createGameDisplay>[];
        startedGames: ReturnType<typeof createGameDisplay>[];
        finishedGames: ReturnType<typeof createGameDisplay>[];
    };
}

const selectHomeScreenView = createSelector(
    selectRootQuery,
    selectListVariantsQuery,
    selectListMyStagingGamesQuery,
    selectListMyStartedGamesQuery,
    selectListMyFinishedGamesQuery,
    (rootQuery, listVariantsQuery, listMyStagingGamesQuery, listMyStartedGamesQuery, listMyFinishedGamesQuery): HomeScreenView => {
        const isLoading =
            rootQuery.isLoading ||
            listVariantsQuery.isLoading ||
            listMyStagingGamesQuery.isLoading ||
            listMyStartedGamesQuery.isLoading ||
            listMyFinishedGamesQuery.isLoading;

        const isSuccess =
            rootQuery.isSuccess &&
            listVariantsQuery.isSuccess &&
            listMyStagingGamesQuery.isSuccess &&
            listMyStartedGamesQuery.isSuccess &&
            listMyFinishedGamesQuery.isSuccess;


        if (!isSuccess) {
            return { isSuccess, isLoading };
        }

        const stagingGames = listMyStagingGamesQuery.data.map((game) =>
            createGameDisplay(game, listVariantsQuery.data, rootQuery.data)
        );

        const startedGames = listMyStartedGamesQuery.data.map((game) =>
            createGameDisplay(game, listVariantsQuery.data, rootQuery.data)
        );

        const finishedGames = listMyFinishedGamesQuery.data.map((game) =>
            createGameDisplay(game, listVariantsQuery.data, rootQuery.data)
        );

        return {
            isLoading,
            isSuccess,
            data: { stagingGames, startedGames, finishedGames },
        };
    }
)

type PlayerInfoView = {
    isLoading: boolean;
    isSuccess: boolean;
    data?: ReturnType<typeof createGameDisplay>;
}

const createSelectPlayerInfoView = (gameId: string) => createSelector(
    selectRootQuery,
    selectListVariantsQuery,
    selectListMyStagingGamesQuery,
    selectListMyStartedGamesQuery,
    selectListMyFinishedGamesQuery,
    (rootQuery, listVariantsQuery, listMyStagingGamesQuery, listMyStartedGamesQuery, listMyFinishedGamesQuery): PlayerInfoView => {
        const isLoading =
            rootQuery.isLoading ||
            listVariantsQuery.isLoading ||
            listMyStagingGamesQuery.isLoading ||
            listMyStartedGamesQuery.isLoading ||
            listMyFinishedGamesQuery.isLoading;

        const isSuccess =
            rootQuery.isSuccess &&
            listVariantsQuery.isSuccess &&
            listMyStagingGamesQuery.isSuccess &&
            listMyStartedGamesQuery.isSuccess &&
            listMyFinishedGamesQuery.isSuccess;


        if (!isSuccess) {
            return { isSuccess, isLoading };
        }

        // Find the game with the given id
        const game = listMyStagingGamesQuery.data.find((game) => game.ID === gameId) ||
            listMyStartedGamesQuery.data.find((game) => game.ID === gameId) ||
            listMyFinishedGamesQuery.data.find((game) => game.ID === gameId);

        if (!game) {
            throw new Error(`Game with id ${gameId} not found`);
        }

        const gameDisplay = createGameDisplay(game, listVariantsQuery.data, rootQuery.data);

        return {
            isLoading,
            isSuccess,
            data: gameDisplay
        };
    }
)

export { selectHomeScreenView, createSelectPlayerInfoView };