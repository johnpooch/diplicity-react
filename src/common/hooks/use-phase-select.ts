import { useSelectedGameContext, useSelectedPhaseContext } from "../context";

/**
 * Encapsulates the logic that drives the PhaseSelect component.
 */
const usePhaseSelect = () => {
    const { gameRetrieveQuery } = useSelectedGameContext();
    const { selectedPhase, setSelectedPhase } = useSelectedPhaseContext();

    const nextDisabled = !gameRetrieveQuery?.data || selectedPhase === gameRetrieveQuery?.data.length;
    const previousDisabled = !gameRetrieveQuery?.data;

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
        query: gameRetrieveQuery,
        handlePhaseSelect,
        handleNext,
        handlePrevious,
        nextDisabled,
        previousDisabled
    };
}

export { usePhaseSelect };