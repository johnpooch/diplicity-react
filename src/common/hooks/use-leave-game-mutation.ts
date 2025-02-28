import service from "../store/service";

/**
 * Encapsulates the logic to leave a game, providing a simplified interface to
 * components.
 */
const useLeaveGameMutation = (gameId: string) => {
    const { endpoints } = service;
    const getRootQuery = endpoints.getRoot.useQuery(undefined);
    const [leaveGameTrigger, leaveGameMutation] = endpoints.leaveGame.useMutation();

    const simplifiedLeaveGameTrigger = () => {
        if (!getRootQuery.data?.Id) throw new Error("No user data found");
        return leaveGameTrigger({
            gameId,
            userId: getRootQuery.data.Id,
        });
    }

    return [simplifiedLeaveGameTrigger, leaveGameMutation] as const;
};

export { useLeaveGameMutation };