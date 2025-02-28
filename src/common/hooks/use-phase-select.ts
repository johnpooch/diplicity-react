import { useSelectedGameContext, useSelectedPhaseContext } from "../context";
import { service } from "../store";
import { mergeQueries } from "./common";

/**
 * Encapsulates the logic that drives the PhaseSelect component.
 */
const usePhaseSelect = () => {
    const { gameId } = useSelectedGameContext();
    const { selectedPhase, setSelectedPhase } = useSelectedPhaseContext();

    const listPhasesQuery = service.endpoints.listPhases.useQuery(gameId);

    const query = mergeQueries([listPhasesQuery], (phases) =>
        phases.map((phase) => ({
            key: phase.PhaseOrdinal,
            label: `${phase.Season} ${phase.Year}, ${phase.Type}`
        }))
    );

    const nextDisabled = !query.data || selectedPhase === query.data.length;
    const previousDisabled = !query.data || selectedPhase === 1;

    const handlePhaseSelect = (phase: number) => {
        setSelectedPhase(phase);
    }
    const handleNext = () => {
        setSelectedPhase(selectedPhase + 1);
    }

    const handlePrevious = () => {
        setSelectedPhase(selectedPhase - 1);
    }

    return {
        selectedPhase,
        query,
        handlePhaseSelect,
        handleNext,
        handlePrevious,
        nextDisabled,
        previousDisabled
    };
}

export { usePhaseSelect };