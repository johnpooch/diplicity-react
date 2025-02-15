import { Stack, Typography, IconButton, Divider } from "@mui/material";
import { NavigateFunction, Outlet, useNavigate } from "react-router";
import { ArrowBack as BackIcon } from "@mui/icons-material";
import { useGameDetailContext } from "../../context";

const styles: Styles = {
  root: {
    flexGrow: 1,
    height: "100vh",
    overflow: "hidden",
  },
  topBar: {
    minHeight: 56,
    flexDirection: "row",
    alignItems: "center",
    padding: 1,
    gap: 1,
    "& h1": {
      margin: 0,
    },
  },
};

type GameDetailSecondaryScreenLayoutProps = {
  title: string | React.ReactNode;
  onNavigateBack: (navigate: NavigateFunction, gameId: string) => void;
};

const GameDetailSecondaryScreenLayout: React.FC<
  GameDetailSecondaryScreenLayoutProps
> = (props) => {
  const { gameId } = useGameDetailContext();
  const navigate = useNavigate();
  return (
    <Stack sx={styles.root}>
      <Stack sx={styles.topBar}>
        <IconButton onClick={() => props.onNavigateBack(navigate, gameId)}>
          <BackIcon />
        </IconButton>
        {typeof props.title === "string" ? (
          <Typography variant="h1">{props.title}</Typography>
        ) : (
          props.title
        )}
      </Stack>
      <Divider />
      <Outlet />
    </Stack>
  );
};

export { GameDetailSecondaryScreenLayout };
