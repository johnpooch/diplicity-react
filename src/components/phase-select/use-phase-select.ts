import service from "../../common/store/service";
import { mergeQueries } from "../../common";
import { useGameDetailContext, useSelectedPhaseContext } from "../../context";

const usePhaseSelect = () => {
    const { gameId } = useGameDetailContext();
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