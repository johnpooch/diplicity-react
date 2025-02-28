import service from "../store/service";

/**
 * Encapsulates the logic to join a game, providing a simplified interface to
 * components.
 */
const useJoinGameMutation = (gameId: string) => {
    const { endpoints } = service;
    const [joinGameTrigger, joinGameMutation] = endpoints.joinGame.useMutation();

    const simplifiedJoinGameTrigger = () => {
        return joinGameTrigger({
            gameId,
            NationPreferences: "",
            GameAlias: "",
        });
    }

    return [simplifiedJoinGameTrigger, joinGameMutation] as const;
};

export { useJoinGameMutation };