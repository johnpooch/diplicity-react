import { Stack, Fab } from "@mui/material";
import { Add as CreateChannelIcon } from "@mui/icons-material";
import { useNavigate } from "react-router";
import { useGameDetailContext } from "../../context";

const styles: Styles = {
  root: {
    flexDirection: "row",
    gap: 1,
  },
};

const CreateChannelAction: React.FC = () => {
  const { gameId } = useGameDetailContext();
  const navigate = useNavigate();

  const handleCreateChannel = () => {
    navigate(`/game/${gameId}/chat/channel/create`);
  };

  return (
    <Stack sx={styles.root}>
      <Fab onClick={handleCreateChannel} color="primary">
        <CreateChannelIcon />
      </Fab>
    </Stack>
  );
};

export { CreateChannelAction };
