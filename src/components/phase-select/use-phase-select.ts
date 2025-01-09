import { useState } from "react";

const usePhaseSelect = () => {
    const [selectedPhase, setSelectedPhase] = useState<number>(1);

    const phases = [
        { key: 1, label: "Spring 1900, Movement" },
        { key: 2, label: "Spring 1900, Retreat" },
        { key: 3, label: "Spring 1900, Adjustment" }
    ]

    const nextDisabled = selectedPhase === phases.length;
    const previousDisabled = selectedPhase === 1;

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
        phases,
        handlePhaseSelect,
        handleNext,
        handlePrevious,
        nextDisabled,
        previousDisabled
    };
}

export { usePhaseSelect };