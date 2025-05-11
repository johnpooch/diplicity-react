import { useSelectedGameContext } from "../context";
import service from "../store/service";

/**
 * Encapsulates the logic to create an order for the currently selected
 * game, providing a simplified interface to components.
 */
const useCreateOrderMutation = () => {
    const { endpoints } = service;
    const { gameId } = useSelectedGameContext();
    const getGameQuery = endpoints.getGame.useQuery(gameId);
    const [createOrderTrigger, createOrderQuery] = service.endpoints.createOrder.useMutation();

    const simplifiedCreateOrderTrigger = (parts: string[]) => {
        if (!getGameQuery.data) throw new Error("No game data found");
        if (!getGameQuery.data.NewestPhaseMeta) throw new Error("No phase meta found");
        return createOrderTrigger({
            Parts: parts,
            phaseId: getGameQuery.data.NewestPhaseMeta.PhaseOrdinal.toString(),
            gameId,
        });
    }

    return [simplifiedCreateOrderTrigger, createOrderQuery] as const;
};

export { useCreateOrderMutation };