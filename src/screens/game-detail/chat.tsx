import React from "react";
import { Stack, Typography, useMediaQuery, useTheme } from "@mui/material";
import { GameDetailAppBar } from "./app-bar";
import { ChannelList } from "./channel-list";

const styles: Styles = {
  container: {
    display: "flex",
    maxWidth: 1000,
    width: "100%",
  },
  channelListContainer: {
    flex: 1,
  },
  channelContainer: {
    flex: 2,
  },
};

const EmptyChannel: React.FC = () => {
  return (
    <Stack
      sx={{
        height: "100%",
        width: "100%",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <Typography>Select a conversation</Typography>
    </Stack>
  );
};

const Chat: React.FC = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  return isMobile ? (
    <ChannelList />
  ) : (
    <Stack sx={styles.container}>
      <GameDetailAppBar />
      <Stack direction="row">
        <Stack sx={styles.channelListContainer}>
          <ChannelList />
        </Stack>
        <Stack sx={styles.channelContainer}>
          <EmptyChannel />
        </Stack>
      </Stack>
    </Stack>
  );
};

export { Chat };
