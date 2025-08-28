import { useSelectedPhaseContext } from "../context";
import { service } from "../store";
import { InteractiveMap } from "./InteractiveMap/InteractiveMap";
import { useSelector } from "react-redux";
import { orderSlice } from "../store/order";
import { useParams } from "react-router";
import { Stack } from "@mui/material";
import { createUseStyles } from "./utils/styles";

const useStyles = createUseStyles(() => ({
  mapContainer: {
    width: "100%",
    height: "100%",
    overflow: "auto",
    minHeight: 0, // This is important for flexbox overflow to work
  },
}));

const GameMap: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  if (!gameId) throw new Error("Game ID is required");

  const styles = useStyles({});
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
    <Stack sx={styles.mapContainer}>
      {
        gameRetrieveQuery.data && ordersListQuery.data && (
          <InteractiveMap
            interactive
            variant={gameRetrieveQuery.data.variant}
            phase={gameRetrieveQuery.data.phases.find(p => p.id === selectedPhase)!}
            orders={ordersListQuery.data}
            orderInProgress={order}
          />
        )
      }
    </Stack >
  )
};

export { GameMap };
