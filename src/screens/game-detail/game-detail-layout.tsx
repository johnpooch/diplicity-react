import React from "react";
import { Outlet } from "react-router";
import {
  GameDetailContextProvider,
  SelectedPhaseContextProvider,
} from "../../context";

const GameDetailLayout: React.FC = () => {
  return (
    <GameDetailContextProvider>
      <SelectedPhaseContextProvider>
        <Outlet />
      </SelectedPhaseContextProvider>
    </GameDetailContextProvider>
  );
};

export { GameDetailLayout };
