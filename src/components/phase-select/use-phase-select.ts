import { useState } from "react";
import service from "../../common/store/service";
import { useParams } from "react-router";
import { mergeQueries } from "../../common";

const usePhaseSelect = () => {
    const { gameId } = useParams<{ gameId: string }>();

    if (!gameId) throw new Error("gameId is required");

    const listPhasesQuery = service.endpoints.listPhases.useQuery(gameId);

    const query = mergeQueries([listPhasesQuery], (phases) =>
        phases.map((phase) => ({
            key: phase.PhaseOrdinal,
            label: `${phase.Season} ${phase.Year}, ${phase.Type}`
        }))
    );

    const [selectedPhase, setSelectedPhase] = useState<number>(1);

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