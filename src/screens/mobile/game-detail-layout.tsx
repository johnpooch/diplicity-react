import {
  GameDetailContextProvider,
  SelectedPhaseContextProvider,
} from "../../context";
import { Outlet } from "react-router";

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
