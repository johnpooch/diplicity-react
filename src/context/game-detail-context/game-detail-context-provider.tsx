import React from "react";
import { useParams } from "react-router";
import { GameDetailContext } from "./game-detail-context";

const GameDetailContextProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const { gameId } = useParams<{ gameId: string }>();

  if (!gameId) throw new Error("gameId is required");

  return (
    <GameDetailContext.Provider value={{ gameId }}>
      {children}
    </GameDetailContext.Provider>
  );
};

export { GameDetailContextProvider };
