import { Stack, Grid2 as Grid, Button } from "@mui/material";
import { createUseStyles } from "../utils/styles";
import { useResponsiveness } from "../utils/responsive";
import { GameDetailSideNavigation } from "../composites/GameDetailSideNavigation";
import { GameDetailBottomNavigation } from "../composites/GameDetailBottomNavigation";
import { Panel } from "../panel";
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
    width: "100%",
    maxHeight: "100%",
  },
  appBarContainer: {
    borderBottom: theme => `1px solid ${theme.palette.divider}`,
  },
  leftPanel: {
    borderRight: theme => `1px solid ${theme.palette.divider}`,
    maxHeight: "100%",
  },
  centerPanel: {
    maxHeight: "100%",
    borderRight: theme => `1px solid ${theme.palette.divider}`,
  },
  rightPanel: {
    borderLeft: theme => `1px solid ${theme.palette.divider}`,
    maxHeight: "100%",
  },
}));

const GameDetailLayout: React.FC<GameDetailLayoutProps> = props => {
  const styles = useStyles(props);
  const responsiveness = useResponsiveness();

  return (
    <>
      <Stack sx={{ flexDirection: "row", height: "100vh" }}>
        {responsiveness.device !== "mobile" && (
          <Stack sx={{}}>
            {props.leftPanel ? props.leftPanel : <GameDetailSideNavigation />}
          </Stack>
        )}
        <Stack sx={{
          flexGrow: responsiveness.device === "mobile" ? 1 : undefined,
          width: responsiveness.device === "mobile" ? "100%" : 300,
          borderRight: theme => `1px solid ${theme.palette.divider}`,
          borderLeft: theme => `1px solid ${theme.palette.divider}`,
          height: responsiveness.device === "mobile" ? "calc(100vh - 56px)" : "100vh",
          overflow: "hidden",
        }}>
          {props.appBar}
          {props.content}
          {responsiveness.device === "mobile" && (
            props.bottomNavigation ? props.bottomNavigation : <GameDetailBottomNavigation />
          )}
        </Stack>
        {responsiveness.device !== "mobile" && (
          <Stack sx={{ flexGrow: 1 }}>
            {props.rightPanel}
          </Stack>
        )}
      </Stack>
    </>
  )
};

export { GameDetailLayout };
