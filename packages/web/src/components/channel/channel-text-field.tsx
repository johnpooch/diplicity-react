import React from "react";
import { Stack, TextField, IconButton } from "@mui/material";
import { Send as SendIcon } from "@mui/icons-material";
import { QueryContainer } from "../query-container";
import {
  useSelectedChannelContext,
  useSelectedGameContext,
} from "../../common";
import { service } from "../../store";

/**
 * The text field for sending messages in a channel.
 */
const ChannelTextField: React.FC = () => {
  const { gameId } = useSelectedGameContext();
  const { channelName: channelId } = useSelectedChannelContext();
  const [message, setMessage] = React.useState("");
  // const query = useGetSelectedChannelQuery();
  // const [createMessage, createMessageMutation] = useCreateMessageMutation();
  const query = service.endpoints.gameChannelsList.useQuery({
    gameId,
  });
  const [createMessage, createMessageMutation] =
    service.endpoints.gameChannelMessageCreate.useMutation();

  const handleSubmit = async () => {
    const result = await createMessage({
      gameId,
      channelId: parseInt(channelId),
      channelMessageCreateRequest: {
        body: message,
      },
    });
    if (result.data) {
      setMessage("");
    }
  };

  const isSubmitting = createMessageMutation.isLoading;

  return (
    <QueryContainer query={query} onRenderLoading={() => <></>}>
      {() => (
        <Stack sx={styles.root} direction="row">
          <TextField
            label="Type a message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            fullWidth
            disabled={isSubmitting}
          />
          <IconButton
            sx={styles.iconButton}
            disabled={message === "" || isSubmitting}
            onClick={handleSubmit}
          >
            <SendIcon />
          </IconButton>
        </Stack>
      )}
    </QueryContainer>
  );
};

const styles: Styles = {
  root: {
    width: "100%",
    gap: 1,
  },
  iconButton: {
    width: 56,
  },
};

export { ChannelTextField };
