import { mergeQueries, service } from "../../../common";

const options = { my: false, mastered: false };

const useFindGames = () => {
    const { endpoints } = service
    const listOpenGamesQuery = endpoints.listGames.useQuery(
        {
            ...options,
            status: "Open",
        },
    );
    return mergeQueries([listOpenGamesQuery], (games) => {
        return games
    });
}

export { useFindGames };