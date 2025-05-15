import { useSelectedGameContext, useSelectedPhaseContext } from "../context";
import { service } from "../store";
import { InteractiveMap } from "./interactive-map/interactive-map";
import { QueryContainer } from "./query-container";
import { useSelector } from "react-redux";
import { orderSlice } from "../store/order";

const Map: React.FC = () => {
  const order = useSelector(orderSlice.selectors.selectOrder);
  const { selectedPhase } = useSelectedPhaseContext();
  const { gameId, gameRetrieveQuery } = useSelectedGameContext();

  const ordersListQuery = service.endpoints.gamePhaseOrdersList.useQuery({
    gameId,
    phaseId: selectedPhase,
  });

  return (
    <QueryContainer query={ordersListQuery}>
      {(orders) => {
        return (
          <QueryContainer query={gameRetrieveQuery}>
            {(game) => {
              const phase = game.phases.find((p) => p.id === selectedPhase);
              if (!phase) throw new Error("Phase not found");
              return (
                <div
                  style={{
                    height: "100%",
                    width: "100%",
                  }}
                >
                  <InteractiveMap
                    interactive
                    variant={game.variant}
                    phase={phase}
                    orders={orders}
                    orderInProgress={order}
                  />
                </div>
              );
            }}
          </QueryContainer>
        );
      }}
    </QueryContainer>
  );
};

export { Map };
