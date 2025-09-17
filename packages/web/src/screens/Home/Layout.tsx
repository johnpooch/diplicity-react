import { Stack, Grid2 as Grid } from "@mui/material";
import { createUseStyles } from "../../components/utils/styles";
import { useResponsiveness } from "../../components/utils/responsive";
import { HomeSideNavigation } from "./SideNavigation";
import { HomeInfoPanel } from "./InfoPanel";
import { HomeBottomNavigation } from "./BottomNavigation";

interface HomeLayoutProps {
  appBar?: React.ReactNode;
  leftPanel?: React.ReactNode;
  rightPanel?: React.ReactNode;
  bottomNavigation?: React.ReactNode;
  content: React.ReactNode;
}

const useStyles = createUseStyles<HomeLayoutProps>(() => ({
  root: {
    alignItems: "center",
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
  rightPanel: {
    borderLeft: theme => `1px solid ${theme.palette.divider}`,
  },
}));

const HomeLayout: React.FC<HomeLayoutProps> = props => {
  const styles = useStyles(props);
  const responsiveness = useResponsiveness();

  return (
    <Stack sx={styles.root}>
      <Grid container sx={styles.container}>
        {responsiveness.device !== "mobile" && (
          <Grid size="auto" sx={styles.leftPanel}>
            {props.leftPanel ? props.leftPanel : <HomeSideNavigation />}
          </Grid>
        )}
        <Grid size="grow" sx={styles.centerPanel}>
          <Stack sx={styles.appBarContainer}>{props.appBar}</Stack>
          {props.content}
        </Grid>
        {responsiveness.device === "desktop" && (
          <Grid size="auto" sx={styles.rightPanel}>
            {props.rightPanel ? props.rightPanel : <HomeInfoPanel />}
          </Grid>
        )}
        {responsiveness.device === "mobile" && (
          <Grid size="auto">
            {props.bottomNavigation ? (
              props.bottomNavigation
            ) : (
              <HomeBottomNavigation />
            )}
          </Grid>
        )}
      </Grid>
    </Stack>
  );
};

export { HomeLayout };
