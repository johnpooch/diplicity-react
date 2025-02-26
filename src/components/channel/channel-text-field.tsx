import React from "react";
import { Stack, TextField, IconButton } from "@mui/material";
import { Send as SendIcon } from "@mui/icons-material";
import { useCreateMessageMutation } from "../../common/hooks/use-create-message-mutation";
import { useGetChannelQuery } from "../../common/hooks/use-get-channel-query";
import { QueryContainer } from "../query-container";

/**
 * The text field for sending messages in a channel.
 */
const ChannelTextField: React.FC = () => {
  const [message, setMessage] = React.useState("");
  const { query } = useGetChannelQuery();
  const [createMessage, createMessageMutation] = useCreateMessageMutation();

  const handleSubmit = async () => {
    const result = await createMessage(message);
    if (result.data) {
      setMessage("");
    }
  };

  const isSubmitting = createMessageMutation.isLoading;

  return (
    <QueryContainer query={query} onRenderLoading={() => <></>}>
      {(data) =>
        data.closed ? null : (
          <Stack sx={styles.root} direction="row">
            <TextField
              label="Type a message"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              fullWidth
              disabled={isSubmitting || data.closed}
            />
            <IconButton
              sx={styles.iconButton}
              disabled={message === "" || isSubmitting || data.closed}
              onClick={handleSubmit}
            >
              <SendIcon />
            </IconButton>
          </Stack>
        )
      }
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
