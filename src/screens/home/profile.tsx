import React, { useState } from "react";
import {
  Avatar,
  Card,
  CardContent,
  Grid2,
  IconButton,
  Menu,
  MenuItem,
  Stack,
  Typography,
} from "@mui/material";
import { MoreHoriz } from "@mui/icons-material";
import { QueryContainer } from "../../components";
import { actions, AppDispatch, service } from "../../common";
import { useDispatch } from "react-redux";
import { ScreenTopBar } from "./screen-top-bar";

const useProfile = () => {
  const dispatch = useDispatch<AppDispatch>();
  const query = service.endpoints.getRoot.useQuery(undefined);
  const handleLogout = () => {
    dispatch(actions.logout());
  };
  return { query, handleLogout };
};

const Profile: React.FC = () => {
  const { query, handleLogout } = useProfile();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const open = Boolean(anchorEl);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const withMenuClose = (fn: () => void) => {
    return () => {
      fn();
      handleMenuClose();
    };
  };

  return (
    <>
      <ScreenTopBar title="Profile" />
      <QueryContainer query={query}>
        {(data) => (
          <Card elevation={0}>
            <CardContent>
              <Stack>
                <Grid2 container spacing={2} alignItems="center">
                  <Grid2 size="auto">
                    <Avatar src={data.Picture} alt={data.Name} />
                  </Grid2>
                  <Grid2 size="grow">
                    <Typography variant="body1" style={{ textAlign: "left" }}>
                      {data.Name}
                    </Typography>
                  </Grid2>
                  <Grid2 size="auto">
                    <IconButton aria-label="menu" onClick={handleMenuClick}>
                      <MoreHoriz />
                    </IconButton>
                    <Menu
                      anchorEl={anchorEl}
                      open={open}
                      onClose={handleMenuClose}
                    >
                      <MenuItem onClick={withMenuClose(handleLogout)}>
                        Logout
                      </MenuItem>
                    </Menu>
                  </Grid2>
                </Grid2>
              </Stack>
            </CardContent>
          </Card>
        )}
      </QueryContainer>
    </>
  );
};

export { Profile };
