import { useSelectedPhaseContext } from "../../context/selected-phase-context/use-selected-phase-context";
import { useGameDetailContext } from "../../context/game-detail-context";
import { useGetCurrentPhaseQuery } from "../../common/hooks/useGetCurrentPhaseQuery";
import { useGetPhaseQuery } from "../../common/hooks/useGetPhaseQuery";
import { mergeQueries } from "../../common";

const useOrderList = () => {
    const { gameId } = useGameDetailContext();
    const { selectedPhase } = useSelectedPhaseContext();

    const currentPhaseQuery = useGetCurrentPhaseQuery(gameId);
    const selectedPhaseQuery = useGetPhaseQuery(gameId, selectedPhase);

    const query = mergeQueries(
        [currentPhaseQuery, selectedPhaseQuery],
        (currentPhase, selectedPhase) => ({
            isCurrentPhase: currentPhase.PhaseOrdinal === selectedPhase.PhaseOrdinal,
        })
    );

    return { query };
};

export { useOrderList };
