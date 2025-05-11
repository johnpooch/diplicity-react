import {
  SelectedGameContextProvider,
  SelectedPhaseContextProvider,
} from "../../context";
import { Outlet } from "react-router";
import { CreateOrderContextProvider } from "../../context/create-order-context-provider";

const GameDetailLayout: React.FC = () => {
  return (
    <SelectedGameContextProvider>
      <SelectedPhaseContextProvider>
        <CreateOrderContextProvider>
          <Outlet />
        </CreateOrderContextProvider>
      </SelectedPhaseContextProvider>
    </SelectedGameContextProvider>
  );
};

export { GameDetailLayout };
