import { createContext } from "react";
import { SelectedPhaseContextType } from "./selected-phase-context.types";

const SelectedPhaseContext = createContext<SelectedPhaseContextType | undefined>(undefined);

export { SelectedPhaseContext };