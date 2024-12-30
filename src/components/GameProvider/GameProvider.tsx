import { createContext, useContext } from "react";
import { useParams } from "react-router";
import {
  createCreateOrderOptions,
  getNewestPhase,
  getVariant,
} from "../../common/utils";
import { useStartedGameQueries } from "../../common/hooks/useGameDetailQueries";
import { GameProviderContextType } from "./GameProvider.types";

const GameProviderContext = createContext<GameProviderContextType | undefined>(
  undefined
);

const GameProvider: React.FC<{
  children: React.ReactNode;
}> = ({ children }) => {
  const { gameId } = useParams<{ gameId: string }>();

  const { listVariantsQuery, getGameQuery, listPhasesQuery, listOptionsQuery } =
    useStartedGameQueries(gameId as string);

  if (
    listVariantsQuery.isLoading ||
    getGameQuery.isLoading ||
    listPhasesQuery.isLoading ||
    listOptionsQuery.isLoading
  ) {
    return <div>Loading...</div>;
  }

  if (
    !listVariantsQuery.isSuccess ||
    !getGameQuery.isSuccess ||
    !listPhasesQuery.isSuccess ||
    !listOptionsQuery.isSuccess
  ) {
    return <div>Error loading data</div>;
  }

  const variant = getVariant(listVariantsQuery.data, getGameQuery.data);
  const phase = getNewestPhase(listPhasesQuery.data, getGameQuery.data);

  const createOrder = {
    options: createCreateOrderOptions(variant, phase, listOptionsQuery.data),
    onSubmit: async (selectedOptions: string[]) => {
      console.log("Submitting create order with options:", selectedOptions);
    },
    onClose: () => {
      console.log("Closing create order");
    },
  };

  return (
    <GameProviderContext.Provider value={{ createOrder }}>
      {children}
    </GameProviderContext.Provider>
  );
};

const useGameProvider = () => {
  const context = useContext(GameProviderContext);
  if (!context) {
    throw new Error("useGameProvider must be used within a GameProvider");
  }
  return context;
};

export { GameProvider, useGameProvider, GameProviderContext };
