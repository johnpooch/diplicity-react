import React, { useState } from "react";
import {
  Card,
  CardContent,
  Grid2 as Grid,
  IconButton,
  Typography,
  Menu,
  MenuItem,
  Avatar,
  Stack,
  Skeleton,
} from "@mui/material";
import { MoreHoriz } from "@mui/icons-material";
import service from "../common/store/service";
import { useDispatch } from "react-redux";
import { AppDispatch } from "../common";
import { authActions } from "../common/store/auth";

const UserInfo: React.FC = () => {
  const rootQuery = service.endpoints.getRoot.useQuery(undefined);
  const dispatch = useDispatch<AppDispatch>();

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

  const onClickLogout = () => {
    dispatch(authActions.logout());
  };

  if (rootQuery.isLoading) {
    return (
      <Card>
        <CardContent>
          <Stack>
            <Grid container spacing={2} alignItems="center">
              <Grid size="auto">
                <Skeleton variant="circular" width={40} height={40} />
              </Grid>
              <Grid size="grow">
                <Skeleton variant="text" width="60%" />
                <Skeleton variant="text" width="40%" />
              </Grid>
              <Grid size="auto">
                <Skeleton variant="circular" width={24} height={24} />
              </Grid>
            </Grid>
          </Stack>
        </CardContent>
      </Card>
    );
  }

  const user = rootQuery.data;

  return (
    <Card elevation={0}>
      <CardContent>
        <Stack>
          <Grid container spacing={2} alignItems="center">
            <Grid size="auto">
              <Avatar src={user?.Picture} alt={user?.Name} />
            </Grid>
            <Grid size="grow">
              <Typography variant="body1" style={{ textAlign: "left" }}>
                {user?.Name}
              </Typography>
            </Grid>
            <Grid size="auto">
              <IconButton aria-label="menu" onClick={handleMenuClick}>
                <MoreHoriz />
              </IconButton>
              <Menu anchorEl={anchorEl} open={open} onClose={handleMenuClose}>
                <MenuItem onClick={withMenuClose(onClickLogout)}>
                  Logout
                </MenuItem>
              </Menu>
            </Grid>
          </Grid>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default UserInfo;
