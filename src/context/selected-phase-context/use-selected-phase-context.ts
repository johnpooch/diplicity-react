import { useContext } from "react";
import { SelectedPhaseContext } from "./selected-phase-context";

const useSelectedPhaseContext = () => {
    const context = useContext(SelectedPhaseContext);
    if (!context) {
        throw new Error("useSelectedPhaseContext must be used within a PhaseProvider");
    }
    return context;
};

export { useSelectedPhaseContext };