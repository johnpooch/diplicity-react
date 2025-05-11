import {
  Stack,
  BottomNavigation,
  BottomNavigationAction,
  AppBar,
  IconButton,
  Typography,
  Divider,
} from "@mui/material";
import {
  Map as MapIcon,
  Chat as ChatIcon,
  Gavel as OrdersIcon,
  ArrowBack as BackIcon,
} from "@mui/icons-material";
import { Outlet, useLocation, useNavigate } from "react-router";
import React, { useEffect, useState } from "react";
import { GameMenu, QueryContainer } from "../../components";
import { service } from "../../store";
import { useSelectedGameContext } from "../../context";

const styles: Styles = {
  root: {
    flexGrow: 1,
    height: "100vh",
    overflow: "hidden",
  },
  appBar: {
    padding: 1,
    alignItems: "center",
    position: "relative",
    display: "flex",
    flexDirection: "row",
    justifyContent: "space-between",
    "& h1": {
      margin: 0,
    },
    gap: 1,
  },
  backButtonTitleContainer: {
    display: "flex",
    flexDirection: "row",
    alignItems: "center",
    width: "100%",
    gap: 1,
  },
  screen: {
    height: "calc(100vh - 120px)",
  },
};

const NavigationItems = [
  {
    label: "Map",
    icon: <MapIcon />,
    value: (gameId: string) => `/game/${gameId}`,
  },
  {
    label: "Orders",
    icon: <OrdersIcon />,
    value: (gameId: string) => `/game/${gameId}/orders`,
  },
  {
    label: "Chat",
    icon: <ChatIcon />,
    value: (gameId: string) => `/game/${gameId}/chat`,
  },
] as const;

type GameDetailPrimaryScreenLayoutProps = {
  title: string | React.ReactNode;
};

const GameDetailPrimaryScreenLayout: React.FC<
  GameDetailPrimaryScreenLayoutProps
> = (props) => {
  const { gameId } = useSelectedGameContext();
  const gameDetailQuery = service.endpoints.gameRetrieve.useQuery({ gameId });
  const navigate = useNavigate();
  const location = useLocation();
  const [navigation, setNavigation] = useState(location.pathname);

  const handleNavigateBack = () => {
    navigate(`/`);
  };

  const handleNavigationChange = (newValue: string) => {
    setNavigation(newValue);
    navigate(newValue);
  };

  useEffect(() => {
    setNavigation(location.pathname);
  }, [location.pathname]);

  return (
    <Stack sx={styles.root}>
      <AppBar sx={styles.appBar} elevation={0}>
        <Stack sx={styles.backButtonTitleContainer}>
          <IconButton onClick={handleNavigateBack}>
            <BackIcon />
          </IconButton>
          {typeof props.title === "string" ? (
            <Typography variant="h1">{props.title}</Typography>
          ) : (
            props.title
          )}
        </Stack>
        <QueryContainer query={gameDetailQuery} onRenderLoading={() => <></>}>
          {(game) => (
            <GameMenu
              game={game}
              onClickGameInfo={(navigate) =>
                navigate(`/game/${gameId}/game-info`)
              }
              onClickPlayerInfo={(navigate) =>
                navigate(`/game/${gameId}/player-info`)
              }
            />
          )}
        </QueryContainer>
      </AppBar>
      <Divider />
      <Stack sx={styles.screen}>
        <Outlet />
      </Stack>
      <BottomNavigation
        value={navigation}
        onChange={(_event, newValue) => handleNavigationChange(newValue)}
      >
        {NavigationItems.map((item) => (
          <BottomNavigationAction
            key={item.value(gameId)}
            label={item.label}
            icon={item.icon}
            value={item.value(gameId)}
          />
        ))}
      </BottomNavigation>
    </Stack>
  );
};

export { GameDetailPrimaryScreenLayout };
