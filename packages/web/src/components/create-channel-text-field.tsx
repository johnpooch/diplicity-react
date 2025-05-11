import { Stack, TextField, IconButton } from "@mui/material";
import { Send as SendIcon } from "@mui/icons-material";
import React from "react";
import { useNavigate } from "react-router";
import { useSelectedGameContext, useCreateChannelContext } from "../context";

/**
 * Text field to create a channel. New channels are created by sending a message
 * to the channel.
 */
const CreateChannelTextField: React.FC = () => {
  const { gameId } = useSelectedGameContext();
  const navigate = useNavigate();
  const [message, setMessage] = React.useState("");

  const { selectedMembers } = useCreateChannelContext();
  const [createChannel, createChannelMutation] = useCreateChannelMutation();

  const isSubmitting = createChannelMutation.isLoading;

  const handleSubmitAndRedirect = async () => {
    const response = await createChannel(message);
    if (response.data) {
      const channelName = response.data.ChannelMembers.join(",");
      navigate(`/game/${gameId}/chat/channel/${channelName}`);
    }
  };

  const disabled =
    selectedMembers.length === 0 || message === "" || isSubmitting;

  return (
    <Stack sx={styles.container}>
      <TextField
        label="Type a message"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        fullWidth
        disabled={isSubmitting}
      />
      <IconButton
        sx={styles.iconButton}
        disabled={disabled}
        onClick={handleSubmitAndRedirect}
      >
        <SendIcon />
      </IconButton>
    </Stack>
  );
};

const styles = {
  container: {
    flexDirection: "row",
    gap: 1,
    width: "100%",
  },
  iconButton: {
    width: 56,
  },
};

export { CreateChannelTextField };
