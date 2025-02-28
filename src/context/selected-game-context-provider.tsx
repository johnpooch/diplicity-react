import React from "react";
import { useParams } from "react-router";
import { SelectedGameContext } from "../common";

const SelectedGameContextProvider: React.FC<{
  children: React.ReactNode | ((gameId: string) => React.ReactNode);
}> = ({ children }) => {
  const { gameId } = useParams<{ gameId: string }>();

  if (!gameId) throw new Error("gameId is required");

  return (
    <SelectedGameContext.Provider value={{ gameId }}>
      {typeof children === "function" ? children(gameId) : children}
    </SelectedGameContext.Provider>
  );
};

export { SelectedGameContextProvider };
