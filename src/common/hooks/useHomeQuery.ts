import { createGameDisplay } from "../display";
import service from "../store/service"

const useHomeQuery = () => {
    const getRootQuery = service.endpoints.getRoot.useQuery(undefined);
    const listVariantsQuery = service.endpoints.listVariants.useQuery(undefined);
    const listStagingGamesQuery = service.endpoints.listGames.useQuery({
        my: true,
        status: "Staging",
        mastered: false,
    });
    const listStartedGamesQuery = service.endpoints.listGames.useQuery({
        my: true,
        status: "Started",
        mastered: false,
    });
    const listFinishedGamesQuery = service.endpoints.listGames.useQuery({
        my: true,
        status: "Finished",
        mastered: false,
    });

    const isLoading = getRootQuery.isLoading || listVariantsQuery.isLoading || listStagingGamesQuery.isLoading || listStartedGamesQuery.isLoading || listFinishedGamesQuery.isLoading;
    const isSuccess = getRootQuery.isSuccess && listVariantsQuery.isSuccess && listStagingGamesQuery.isSuccess && listStartedGamesQuery.isSuccess && listFinishedGamesQuery.isSuccess;
    const isError = getRootQuery.isError || listVariantsQuery.isError || listStagingGamesQuery.isError || listStartedGamesQuery.isError || listFinishedGamesQuery.isError;

    if (!isSuccess) {
        return {
            isLoading,
            isSuccess,
            isError,
        }
    }

    return {
        isLoading,
        isSuccess,
        isError,
        data: {
            root: getRootQuery.data,
            variants: listVariantsQuery.data,
            stagingGames: listStagingGamesQuery.data.map((game) => createGameDisplay(game, listVariantsQuery.data, getRootQuery.data)),
            startedGames: listStartedGamesQuery.data.map((game) => createGameDisplay(game, listVariantsQuery.data, getRootQuery.data)),
            finishedGames: listFinishedGamesQuery.data.map((game) => createGameDisplay(game, listVariantsQuery.data, getRootQuery.data)),
        },
    }
}

export { useHomeQuery };