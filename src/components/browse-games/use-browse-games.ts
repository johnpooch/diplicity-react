import { mergeQueries } from "../../common";
import service from "../../common/store/service";
import { createGameCardProps } from "../game-card";

const options = { my: false, mastered: false };

const useBrowseGames = () => {
    const { endpoints } = service
    const listOpenGamesQuery = endpoints.listGames.useQuery(
        {
            ...options,
            status: "Open",
        },
    );
    return mergeQueries([listOpenGamesQuery], (games) => {
        return games.map(createGameCardProps)
    });
}

export { useBrowseGames };