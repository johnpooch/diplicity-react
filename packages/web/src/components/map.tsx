import { useSelectedPhaseContext } from "../context";
import { service } from "../store";
import { InteractiveMap } from "./interactive-map/interactive-map";
import { QueryContainer } from "./query-container";
import { useSelector } from "react-redux";
import { orderSlice } from "../store/order";
import { useParams } from "react-router";
import { Stack } from "@mui/material";

const Map: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("Game ID is required");

  const { selectedPhase } = useSelectedPhaseContext();

  const order = useSelector(orderSlice.selectors.selectOrder);

  const gameRetrieveQuery = service.endpoints.gameRetrieve.useQuery({
    gameId,
  });

  const ordersListQuery = service.endpoints.gamePhaseOrdersList.useQuery({
    gameId,
    phaseId: selectedPhase,
  });

  return (
    <QueryContainer query={ordersListQuery}>
      {orders => {
        return (
          <QueryContainer query={gameRetrieveQuery}>
            {game => {
              const phase = game.phases.find(p => p.id === selectedPhase);
              if (!phase) throw new Error("Phase not found");
              return (
                <Stack sx={{
                  width: "100%",
                  height: "100%",
                  overflow: "auto",
                  minHeight: 0 // This is important for flexbox overflow to work
                }}>

                  <InteractiveMap
                    interactive
                    variant={game.variant}
                    phase={phase}
                    orders={orders}
                    orderInProgress={order}
                  />
                </Stack>
              );
            }}
          </QueryContainer>
        );
      }}
    </QueryContainer>
  );
};

export { Map };
