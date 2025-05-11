import React from "react";
import { useParams } from "react-router";
import { SelectedGameContext } from "../common";
import { service } from "../store";

type Query<TData> = {
  isLoading: boolean;
  isError: boolean;
  data?: TData;
};

const SelectedGameContextProvider: React.FC<{
  children:
    | React.ReactNode
    | ((props: {
        gameId: number;
        gameRetrieveQuery: Query<
          typeof service.endpoints.gameRetrieve.Types.ResultType
        >;
      }) => React.ReactNode);
}> = ({ children }) => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("gameId is required");
  const gameIdAsNumber = parseInt(gameId, 10);

  const gameRetrieveQuery = service.endpoints.gameRetrieve.useQuery({
    gameId: gameIdAsNumber,
  });

  return (
    <SelectedGameContext.Provider
      value={{ gameId: gameIdAsNumber, gameRetrieveQuery }}
    >
      {typeof children === "function"
        ? children({
            gameId: gameIdAsNumber,
            gameRetrieveQuery,
          })
        : children}
    </SelectedGameContext.Provider>
  );
};

export { SelectedGameContextProvider };
