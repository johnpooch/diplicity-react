import React from "react";
import { AppBar, IconButton, Stack, Typography } from "@mui/material";
import {
  ArrowBack as BackIcon,
  Add as CreateChannelIcon,
} from "@mui/icons-material";
import { Outlet, useNavigate } from "react-router";

const ChannelListLayout: React.FC = () => {
  const navigate = useNavigate();

  const handleCreateChannel = () => {
    navigate("create-channel");
  };

  const handleBack = () => {
    navigate("/");
  };

  return (
    <Stack>
      <AppBar
        position="static"
        elevation={0}
        sx={(theme) => ({
          borderBottom: `1px solid ${theme.palette.divider}`,
        })}
      >
        <Stack
          sx={{
            paddingLeft: 2,
            paddingRight: 2,
            paddingTop: 1,
            paddingBottom: 1,
          }}
          direction="row"
          justifyContent="space-between"
        >
          <Stack direction="row" alignItems="center" gap={1}>
            <IconButton edge="start" color="inherit" onClick={handleBack}>
              <BackIcon />
            </IconButton>
            <Typography variant="h1" sx={{ marginBottom: 0 }}>
              Conversations
            </Typography>
          </Stack>
          <IconButton
            edge="start"
            color="inherit"
            onClick={handleCreateChannel}
          >
            <CreateChannelIcon />
          </IconButton>
        </Stack>
      </AppBar>
      <Outlet />
    </Stack>
  );
};

export { ChannelListLayout };
