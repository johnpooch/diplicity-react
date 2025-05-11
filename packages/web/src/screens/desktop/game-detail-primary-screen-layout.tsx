import { Stack, Tabs, Tab, Divider } from "@mui/material";
import { Outlet, useLocation, useNavigate } from "react-router";
import { useSelectedGameContext } from "../../context";

const GameDetailPrimaryScreenLayout: React.FC = () => {
  const { gameId } = useSelectedGameContext();
  const location = useLocation();
  const navigate = useNavigate();

  const currentTab = location.pathname.endsWith("chat") ? "chat" : "orders";

  const handleTabChange = (_: unknown, newValue: string) => {
    navigate(`/game/${gameId}/${newValue}`);
  };

  return (
    <Stack sx={styles.root}>
      <Tabs variant="fullWidth" value={currentTab} onChange={handleTabChange}>
        <Tab label="Orders" value="orders" />
        <Tab label="Chat" value="chat" />
      </Tabs>
      <Divider />
      <Outlet />
    </Stack>
  );
};

const styles: Styles = {
  root: {
    flexGrow: 1,
  },
};

export { GameDetailPrimaryScreenLayout };
