import { Stack, Fab } from "@mui/material";
import { Add as CreateChannelIcon } from "@mui/icons-material";
import { useNavigate } from "react-router";
import { useSelectedGameContext } from "../../common";

/**
 * Button to open the create channel dialog.
 */
const CreateChannelAction: React.FC = () => {
  const { gameId } = useSelectedGameContext();
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

const styles: Styles = {
  root: {
    flexDirection: "row",
    gap: 1,
  },
};

export { CreateChannelAction };
