import {
  AppBar,
  BottomNavigation,
  BottomNavigationAction,
} from "@mui/material";
import {
  Map as MapIcon,
  Gavel as OrdersIcon,
  People as PlayersIcon,
} from "@mui/icons-material";
import { useLocation, useNavigate, useParams } from "react-router";

const GameDetailsNavigation: React.FC = () => {
  const { gameId } = useParams<{ gameId: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  if (!gameId) throw new Error("gameId is required");

  const navigationPathMap = {
    map: `/game/${gameId}`,
    orders: `/game/${gameId}/orders`,
    players: `/game/${gameId}/players`,
  } as const;

  console.log(location);

  return (
    <AppBar position="fixed" color="primary" sx={{ top: "auto", bottom: 0 }}>
      <BottomNavigation
        value={location.pathname}
        onChange={(_event, value) => {
          navigate(value);
        }}
      >
        <BottomNavigationAction
          label="Map"
          icon={<MapIcon />}
          value={navigationPathMap.map}
        />
        <BottomNavigationAction
          label="Orders"
          icon={<OrdersIcon />}
          value={navigationPathMap.orders}
        />
        <BottomNavigationAction
          label="Players"
          icon={<PlayersIcon />}
          value={navigationPathMap.players}
        />
      </BottomNavigation>
    </AppBar>
  );
};

export { GameDetailsNavigation };
