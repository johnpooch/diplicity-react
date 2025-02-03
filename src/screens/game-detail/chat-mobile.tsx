import React from "react";
import { Fab, Stack } from "@mui/material";
import { Add as CreateChannelIcon } from "@mui/icons-material";
import { ChannelList } from "../../components";
import { useNavigate } from "react-router";
import { useGameDetailContext } from "../../context";

const styles: Styles = {
  fab: {
    position: "fixed",
    bottom: 72, // 56px for bottom navigation + 16px margin
    right: 16,
  },
};

const ChannelListMobile: React.FC = () => {
  const { gameId } = useGameDetailContext();
  const navigate = useNavigate();

  const handleCreateChannel = () => {
    navigate(`/game/${gameId}/chat/create-channel`);
  };

  return (
    <Stack>
      <ChannelList />
      <Fab
        sx={styles.fab}
        color="primary"
        aria-label="create order"
        onClick={handleCreateChannel}
      >
        <CreateChannelIcon />
      </Fab>
    </Stack>
  );
};

export { ChannelListMobile };
