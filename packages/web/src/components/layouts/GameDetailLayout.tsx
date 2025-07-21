import { Stack, Grid2 as Grid } from "@mui/material";
import { createUseStyles } from "../utils/styles";
import { useResponsiveness } from "../utils/responsive";
import { GameDetailSideNavigation } from "../composites/GameDetailSideNavigation";
// import { GameDetailBottomNavigation } from "../composites/GameDetailBottomNavigation";

interface GameDetailLayoutProps {
  appBar?: React.ReactNode;
  leftPanel?: React.ReactNode;
  rightPanel?: React.ReactNode;
  bottomNavigation?: React.ReactNode;
  content: React.ReactNode;
}

const useStyles = createUseStyles<GameDetailLayoutProps>(() => ({
  root: {
    alignItems: "center",
    height: "100vh",
  },
  container: {
    display: "flex",
    justifyContent: "center",
    flexGrow: 1,
    maxWidth: 1000,
    width: "100%",
  },
  leftPanel: {
    borderRight: theme => `1px solid ${theme.palette.divider}`,
  },
  appBarContainer: {
    borderBottom: theme => `1px solid ${theme.palette.divider}`,
  },
  centerPanel: {},
}));

const GameDetailLayout: React.FC<GameDetailLayoutProps> = props => {
  const styles = useStyles(props);
  const responsiveness = useResponsiveness();

  return (
    <Stack sx={styles.root}>
      <Grid container sx={styles.container}>
        {responsiveness.device !== "mobile" && (
          <Grid size="auto" sx={styles.leftPanel}>
            {props.leftPanel ? props.leftPanel : <GameDetailSideNavigation />}
          </Grid>
        )}
        <Grid size="grow" sx={styles.centerPanel}>
          <Stack sx={{ height: "100%" }}>
            <Stack sx={styles.appBarContainer}>{props.appBar}</Stack>
            {props.content}
          </Stack>
        </Grid>
      </Grid>
    </Stack>
  );
};

export { GameDetailLayout };
