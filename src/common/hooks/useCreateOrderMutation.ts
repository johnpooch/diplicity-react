import service from "../store/service";

const useCreateOrderMutation = (gameId: string) => {
    const { endpoints } = service;
    const getGameQuery = endpoints.getGame.useQuery(gameId);
    const [createOrderTrigger, createOrderQuery] = service.endpoints.createOrder.useMutation();

    const simplifiedCreateOrderTrigger = (parts: string[]) => {
        if (!getGameQuery.data) throw new Error("No game data found");
        if (!getGameQuery.data.NewestPhaseMeta) throw new Error("No phase meta found");
        createOrderTrigger({
            Parts: parts,
            phaseId: getGameQuery.data.NewestPhaseMeta.PhaseOrdinal.toString(),
            gameId,
        });
    }

    return [simplifiedCreateOrderTrigger, createOrderQuery] as const;
};

export { useCreateOrderMutation };