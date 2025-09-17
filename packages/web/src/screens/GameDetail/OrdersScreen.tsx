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

    const ordersListQuery = service.endpoints.gamePhaseOrdersList.useQuery({
        gameId,
        phaseId: selectedPhase,
    });

    const [confirmOrders, confirmOrdersMutation] =
        service.endpoints.gameConfirmCreate.useMutation();

    const handleConfirmOrders = async () => {
        await confirmOrders({ gameId }).unwrap();
    };

    if (
        gameRetrieveQuery.isError ||
        !gameRetrieveQuery.data ||
        ordersListQuery.isError ||
        !ordersListQuery.data
    ) {
        return null;
    }

    const game = gameRetrieveQuery.data;
    const orders = ordersListQuery.data;
    const currentPhase = game.phases.find(p => p.id === selectedPhase)!;
    const userNation = game.members.find(m => m.isCurrentUser)!.nation;

    return (
        <GameDetailLayout
            appBar={<GameDetailAppBar title={<PhaseSelect />} onNavigateBack={() => navigate("/")} />}
            rightPanel={<GameMap />}
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
                    <InactivePhaseOrders
                        phase={currentPhase}
                        nationOrders={orders}
                        provinces={game.variant.provinces}
                    />
                )
            }
        />
    );
};

export { OrdersScreen };

