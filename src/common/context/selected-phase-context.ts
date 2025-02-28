import { createContext, useContext } from "react";

/**
 * Context to provide and set the currently selected phase.
 */
const SelectedPhaseContext = createContext<SelectedPhaseContextType | undefined>(undefined);

const useSelectedPhaseContext = () => {
    const context = useContext(SelectedPhaseContext);
    if (!context) {
        throw new Error("useSelectedPhaseContext must be used within a PhaseProvider");
    }
    return context;
};

type SelectedPhaseContextType = {
    selectedPhase: number;
    setSelectedPhase: (phase: number) => void;
}

export { SelectedPhaseContext, useSelectedPhaseContext };