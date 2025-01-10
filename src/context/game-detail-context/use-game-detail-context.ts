import { useContext } from "react";
import { GameDetailContext } from "./game-detail-context";

const useGameDetailContext = () => {
    const context = useContext(GameDetailContext);
    if (!context) {
        throw new Error("useGameDetailContext must be used within a PhaseProvider");
    }
    return context;
};

export { useGameDetailContext };