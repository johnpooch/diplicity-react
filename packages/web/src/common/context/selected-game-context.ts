import { createContext, useContext } from "react";
import { service } from "../../store";

type Query<TData> = {
    isLoading: boolean;
    isError: boolean;
    data?: TData;
};

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
    gameId: number;
    gameRetrieveQuery: Query<
        typeof service.endpoints.gameRetrieve.Types.ResultType
    >;
}

export { SelectedGameContext, useSelectedGameContext };