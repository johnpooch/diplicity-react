import { Stack } from "@mui/material";
import { createUseStyles } from "../../utils/styles";
import { useResponsiveness } from "../../utils/responsive";
import { GameDetailSideNavigation } from "./SideNavigation";
import { GameDetailBottomNavigation } from "./BottomNavigation";

interface GameDetailLayoutProps {
  appBar?: React.ReactNode;
  leftPanel?: React.ReactNode;
  rightPanel?: React.ReactNode;
  bottomNavigation?: React.ReactNode;
  content: React.ReactNode;
}

const useStyles = createUseStyles<GameDetailLayoutProps>((_props, theme) => ({
  root: {
    flexDirection: "row",
    height: "100vh"
  },
  container: {

  },
  appBarContainer: {

  },
  leftPanel: {

  },
  centerPanel: {
    flexGrow: 1,
    width: 300,
    borderRight: `1px solid ${theme.palette.divider}`,
    borderLeft: `1px solid ${theme.palette.divider}`,
    height: "100vh",
    overflow: "hidden"
  },
  centerPanelMobile: {
    flexGrow: 1,
    width: "100%",
    borderRight: `1px solid ${theme.palette.divider}`,
    borderLeft: `1px solid ${theme.palette.divider}`,
    height: "calc(100vh - 56px)",
    overflow: "hidden"
  },
  rightPanel: {
    flexGrow: 1
  }
}));

const GameDetailLayout: React.FC<GameDetailLayoutProps> = props => {
  const styles = useStyles(props);
  const responsiveness = useResponsiveness();

  return (
    <Stack sx={styles.root}>
      {responsiveness.device !== "mobile" && (
        <Stack sx={styles.leftPanel}>
          {props.leftPanel ? props.leftPanel : <GameDetailSideNavigation />}
        </Stack>
      )}
      <Stack sx={responsiveness.device === "mobile" ? styles.centerPanelMobile : styles.centerPanel}>
        {props.appBar}
        {props.content}
        {responsiveness.device === "mobile" && (
          props.bottomNavigation ? props.bottomNavigation : <GameDetailBottomNavigation />
        )}
      </Stack>
      {responsiveness.device !== "mobile" && (
        <Stack sx={styles.rightPanel}>
          {props.rightPanel}
        </Stack>
      )}
    </Stack>
  )
};

export { GameDetailLayout };
