import { createGameDisplay } from "../display";
import service from "../store/service";

const useGameInfoQuery = (gameId: string) => {
    const getRootQuery = service.endpoints.getRoot.useQuery(undefined);
    const listVariantsQuery = service.endpoints.listVariants.useQuery(undefined);
    const getGameQuery = service.endpoints.getGame.useQuery(gameId);

    const isLoading = getRootQuery.isLoading || listVariantsQuery.isLoading || getGameQuery.isLoading;
    const isSuccess = getRootQuery.isSuccess && listVariantsQuery.isSuccess && getGameQuery.isSuccess;
    const isError = getRootQuery.isError || listVariantsQuery.isError || getGameQuery.isError;

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
        data: createGameDisplay(getGameQuery.data, listVariantsQuery.data, getRootQuery.data),
    }
}

export { useGameInfoQuery };
