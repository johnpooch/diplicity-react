import service from "../store/service";

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