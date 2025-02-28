import { createContext, useContext } from "react";

/**
 * Context to provide the currently selected game.
 */
const SelectedGameContext = createContext<SelectedGameContextType | undefined>(undefined);

const useSelectedGameContext = () => {
    const context = useContext(SelectedGameContext);
    if (!context) {
        throw new Error("useSelectedGameContext must be used within a GameDetailProvider");
    }
    return context;
};

type SelectedGameContextType = {
    gameId: string;
}

export { SelectedGameContext, useSelectedGameContext };