import { Stack } from "@mui/material";
import { createUseStyles } from "../utils/styles";
import { useResponsiveness } from "../utils/responsive";
import { Outlet } from "react-router";
import { Map } from "../map";

const useStyles = createUseStyles(() => ({
  root: {
    width: "100%",
  },
  container: {
    width: "100%",
    height: "100vh",
    flexDirection: "row",
  },
  contentPanel: {
    flex: 1,
    boxShadow: 2,
  },
  mapPanel: {
    flex: 3,
    height: "100%",
    justifyContent: "center",
    gap: 2,
  },
}));

const GameDetailMapLayout: React.FC = props => {
  const styles = useStyles(props);
  const responsiveness = useResponsiveness();

  if (responsiveness.device === "mobile") {
    return <Outlet />;
  }

  return (
    <Stack sx={styles.root}>
      <Stack sx={styles.container}>
        <Stack sx={styles.contentPanel}>
          <Outlet />
        </Stack>
        <Stack sx={styles.mapPanel}>
          <Map />
        </Stack>
      </Stack>
    </Stack>
  );
};

export { GameDetailMapLayout };
