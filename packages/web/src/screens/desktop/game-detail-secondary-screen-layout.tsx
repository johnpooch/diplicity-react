import { Stack, Divider } from "@mui/material";
import { NavigateFunction, Outlet, useNavigate } from "react-router";
import { IconButton } from "../../components/elements/Button";
import { IconName } from "../../components/elements/Icon";
import { AppBar } from "../../components/elements/AppBar";
import { useSelectedGameContext } from "../../context";

type GameDetailSecondaryScreenLayoutProps = {
  title: string;
  onNavigateBack: (navigate: NavigateFunction, gameId: string) => void;
};

const GameDetailSecondaryScreenLayout: React.FC<
  GameDetailSecondaryScreenLayoutProps
> = (props) => {
  const navigate = useNavigate();
  const { gameId } = useSelectedGameContext();

  return (
    <Stack sx={styles.root}>
      <AppBar title={props.title} leftButton={
        <IconButton
          icon={IconName.Back}
          onClick={() => props.onNavigateBack(navigate, gameId)}
        />}
      />
      <Divider />
      <Outlet />
    </Stack>
  );
};

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

export { GameDetailSecondaryScreenLayout };
