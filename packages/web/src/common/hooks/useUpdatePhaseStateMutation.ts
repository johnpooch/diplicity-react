import service from "../store/service";
import { useGetCurrentPhaseQuery } from "./use-get-current-phase-query";

type PhaseState = {
    isConfirmed: boolean;
};

const useUpdatePhaseStateMutation = (gameId: string) => {
    const { endpoints } = service;
    const getCurrentPhaseQuery = useGetCurrentPhaseQuery(gameId);
    const [updatePhaseStateTrigger, updatePhaseStateMutation] = endpoints.updatePhaseState.useMutation();

    const simplifiedUpdatePhaseStateTrigger = (phaseState: PhaseState) => {
        if (!getCurrentPhaseQuery.data) throw new Error("No phase data found");
        return updatePhaseStateTrigger({
            GameID: gameId,
            PhaseOrdinal: getCurrentPhaseQuery.data.PhaseOrdinal,
            ReadyToResolve: phaseState.isConfirmed,
        });
    }

    return [simplifiedUpdatePhaseStateTrigger, updatePhaseStateMutation] as const;
};

export { useUpdatePhaseStateMutation };