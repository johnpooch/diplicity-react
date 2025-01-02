import { mergeQueries } from "../../common";
import service from "../../common/store/service";
import { createGameCardProps } from "../game-card";

const options = { my: true, mastered: false };

const useHome = () => {
    const { endpoints } = service
    const listStagingGamesQuery = endpoints.listGames.useQuery(
        {
            ...options,
            status: "Staging",
        },
    );
    const listStartedGamesQuery = endpoints.listGames.useQuery({
        ...options,
        status: "Started",
    });
    const listFinishedGamesQuery = endpoints.listGames.useQuery({
        ...options,
        status: "Finished",
    });
    return mergeQueries([listStagingGamesQuery, listStartedGamesQuery, listFinishedGamesQuery], (stagingGames, startedGames, finishedGames) => {
        const stagingGameCards = stagingGames.map(createGameCardProps)
        const startedGameCards = startedGames.map(createGameCardProps)
        const finishedGameCards = finishedGames.map(createGameCardProps)
        return {
            stagingGameCards,
            startedGameCards,
            finishedGameCards,
        }
    });
}

export { useHome };