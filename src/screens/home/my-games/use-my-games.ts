import { mergeQueries, service } from "../../../common";

const options = { my: true, mastered: false };

const useMyGames = () => {
    const { endpoints } = service
    const listVariantsQuery = endpoints.listVariants.useQuery(undefined);
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
    return mergeQueries([listVariantsQuery, listStagingGamesQuery, listStartedGamesQuery, listFinishedGamesQuery], (variants, stagingGames, startedGames, finishedGames) => {
        const getMapSvgUrl = (game: typeof stagingGames[number]) => {
            const variant = variants.find((variant) => variant.Name === game.Variant);
            return variant?.Links?.find((link) => link.Rel === "map")?.URL
        }
        return {
            getMapSvgUrl,
            stagingGames,
            startedGames,
            finishedGames,
        }
    });
}

export { useMyGames };