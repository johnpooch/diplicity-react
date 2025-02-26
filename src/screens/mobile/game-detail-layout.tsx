import {
  GameDetailContextProvider,
  SelectedPhaseContextProvider,
} from "../../context";
import { Outlet } from "react-router";
import { CreateOrderContextProvider } from "../../context/create-order-context";

const GameDetailLayout: React.FC = () => {
  return (
    <GameDetailContextProvider>
      <SelectedPhaseContextProvider>
        <CreateOrderContextProvider>
          <Outlet />
        </CreateOrderContextProvider>
      </SelectedPhaseContextProvider>
    </GameDetailContextProvider>
  );
};

export { GameDetailLayout };
