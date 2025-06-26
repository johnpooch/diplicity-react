
import React, { createContext, useContext } from "react";
import { useParams } from "react-router";
import { service } from "../store";

type Query<TData> = {
  isLoading: boolean;
  isError: boolean;
  data?: TData;
};

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
  gameRetrieveQuery: Query<
    typeof service.endpoints.gameRetrieve.Types.ResultType
  >;
}

const SelectedGameContextProvider: React.FC<{
  children:
  | React.ReactNode
  | ((props: {
    gameId: string;
    gameRetrieveQuery: Query<
      typeof service.endpoints.gameRetrieve.Types.ResultType
    >;
  }) => React.ReactNode);
}> = ({ children }) => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("gameId is required");

  const gameRetrieveQuery = service.endpoints.gameRetrieve.useQuery({
    gameId,
  });

  return (
    <SelectedGameContext.Provider
      value={{ gameId, gameRetrieveQuery }}
    >
      {typeof children === "function"
        ? children({
          gameId,
          gameRetrieveQuery,
        })
        : children}
    </SelectedGameContext.Provider>
  );
};

export { SelectedGameContextProvider, useSelectedGameContext };
