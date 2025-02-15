import React from "react";
import { useParams } from "react-router";
import { GameDetailContext } from "./game-detail-context";

const GameDetailContextProvider: React.FC<{
  children: React.ReactNode | ((gameId: string) => React.ReactNode);
}> = ({ children }) => {
  const { gameId } = useParams<{ gameId: string }>();

  if (!gameId) throw new Error("gameId is required");

  return (
    <GameDetailContext.Provider value={{ gameId }}>
      {typeof children === "function" ? children(gameId) : children}
    </GameDetailContext.Provider>
  );
};

export { GameDetailContextProvider };
