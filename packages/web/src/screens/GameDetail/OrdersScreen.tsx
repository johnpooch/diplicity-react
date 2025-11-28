import React from "react";
import { service } from "../../store";
import { GameDetailAppBar } from "./AppBar";
import { GameDetailLayout } from "./Layout";
import { useNavigate } from "react-router";
import { PhaseSelect } from "../../components/PhaseSelect";
import { useSelectedGameContext, useSelectedPhaseContext } from "../../context";
import { GameMap } from "../../components/GameMap";
import { ActivePhaseOrders } from "./ActivePhaseOrders";
import { InactivePhaseOrders } from "./InactivePhaseOrders";

const OrdersScreen: React.FC = () => {
  const { gameId, gameRetrieveQuery } = useSelectedGameContext();

  const navigate = useNavigate();
  const { selectedPhase } = useSelectedPhaseContext();

  const phaseQuery = service.endpoints.gamePhaseRetrieve.useQuery({
    gameId,
    phaseId: selectedPhase,
  });

  const ordersListQuery = service.endpoints.gameOrdersList.useQuery({
    gameId,
    phaseId: selectedPhase,
  });

  const [confirmOrders, confirmOrdersMutation] =
    service.endpoints.gameConfirmPhasePartialUpdate.useMutation();

  const handleConfirmOrders = async () => {
    await confirmOrders({
      gameId,
      patchedPhaseState: { ordersConfirmed: true },
    }).unwrap();
  };

  if (
    gameRetrieveQuery.isError ||
    !gameRetrieveQuery.data ||
    phaseQuery.isError ||
    !phaseQuery.data ||
    ordersListQuery.isError ||
    !ordersListQuery.data
  ) {
    return null;
  }

  const game = gameRetrieveQuery.data;
  const currentPhase = phaseQuery.data;
  const userNation = game.members.find(m => m.isCurrentUser)!.nation ?? "";

  return (
    <GameDetailLayout
      appBar={
        <GameDetailAppBar
          title={<PhaseSelect />}
          onNavigateBack={() => navigate("/")}
        />
      }
      content={
        currentPhase.status === "active" ? (
          <ActivePhaseOrders
            phase={currentPhase}
            userNation={userNation}
            onConfirmOrders={handleConfirmOrders}
            isPhaseConfirmed={game.phaseConfirmed}
            isConfirming={confirmOrdersMutation.isLoading}
          />
        ) : (
          <InactivePhaseOrders />
        )
      }
      rightPanel={<GameMap />}
    />
  );
};

export { OrdersScreen };
