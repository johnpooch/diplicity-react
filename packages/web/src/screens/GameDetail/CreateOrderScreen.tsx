import React, { useEffect } from "react";
import { service } from "../../store";
import { GameDetailAppBar } from "./AppBar";
import { GameDetailLayout } from "./Layout";
import { useNavigate, useParams } from "react-router";
import { GameMap } from "../../components/GameMap";
import { Panel } from "../../components/Panel";
import { useSelectedGameContext, useSelectedPhaseContext } from "../../context";
import { useSelector } from "react-redux";
import { orderSlice } from "../../store/order";

const CreateOrderScreen: React.FC = () => {
    const { gameId } = useSelectedGameContext();
    const { selectedPhase } = useSelectedPhaseContext();

    const order = useSelector(orderSlice.selectors.selectOrder);

    const navigate = useNavigate();

    const [getOptions, optionsQuery] = service.endpoints.gamePhaseOptionsCreate.useMutation();

    useEffect(() => {
        getOptions({
            gameId,
            phaseId: selectedPhase,
            listOptionsRequest: {
                order: order
            },
        });
    }, [getOptions, gameId, order]);

    const gameRetrieveQuery = service.endpoints.gameRetrieve.useQuery({
        gameId,
    });

    if (gameRetrieveQuery.isError || !gameRetrieveQuery.data) {
        return null;
    }

    const game = gameRetrieveQuery.data;

    return (
        <GameDetailLayout
            appBar={
                <GameDetailAppBar
                    title="Create Order"
                    onNavigateBack={() => navigate(`/game/${gameId}/orders`)}
                    variant="secondary"
                />
            }
            rightPanel={
                <GameMap />
            }
            content={
                <Panel>
                    <Panel.Content>
                        {/* TODO: Add order creation form here */}
                        <p>Order creation form will go here</p>
                    </Panel.Content>
                </Panel>
            }
        />
    );
};

export { CreateOrderScreen };
