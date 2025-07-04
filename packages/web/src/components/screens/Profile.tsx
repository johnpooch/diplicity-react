import React, { useState } from "react";
import {
  Avatar,
  Grid2,
  FormControl,
  FormControlLabel,
  Menu,
  MenuItem,
  Stack,
  Switch,
  Typography,
  Divider,
  Skeleton,
} from "@mui/material";
import { HomeLayout } from "../layouts/HomeLayout";
import { authSlice, service } from "../../store";
import { NotificationBanner } from "../notification-banner";
import { HomeAppBar } from "../composites/HomeAppBar";
import { IconName } from "../elements/Icon";
import { IconButton } from "../elements/Button";
import { useMessaging } from "../../context";
import { useDispatch } from "react-redux";

const Profile: React.FC = () => {
  const dispatch = useDispatch();
  const query = service.endpoints.userRetrieve.useQuery();
  const { enableMessaging, enabled, disableMessaging } = useMessaging();

  const handleLogout = () => {
    dispatch(authSlice.actions.logout());
  };

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

  if (query.isError) {
    return <div>Error</div>;
  }

  return (
    <HomeLayout
      appBar={<HomeAppBar title="Profile" />}
      content={
        <Stack>
          <NotificationBanner />
          <Grid2 container p={2} alignItems="center" gap={2}>
            <Grid2 size="auto">
              {query.isLoading ? (
                <Skeleton variant="circular" width={40} height={40} />
              ) : (
                <Avatar src={query.data?.picture} alt={query.data?.username} />
              )}
            </Grid2>
            <Grid2 size="grow">
              {query.isLoading ? (
                <Skeleton variant="text" width={150} height={24} />
              ) : (
                <Typography variant="body1">{query.data?.username}</Typography>
              )}
            </Grid2>
            <Grid2 size="auto">
              <IconButton
                aria-label="menu"
                onClick={handleMenuClick}
                icon={IconName.Menu}
              />
              <Menu anchorEl={anchorEl} open={open} onClose={handleMenuClose}>
                <MenuItem onClick={withMenuClose(handleLogout)}>
                  Logout
                </MenuItem>
              </Menu>
            </Grid2>
          </Grid2>
          <Divider />
          <Stack p={2} gap={2}>
            <Typography variant="h4">Notifications</Typography>
            <Stack>
              <FormControl>
                <FormControlLabel
                  control={
                    <Switch
                      checked={enabled}
                      onChange={(_, checked) => {
                        if (checked) {
                          enableMessaging();
                        } else {
                          disableMessaging();
                        }
                      }}
                      name="pushNotifications"
                    />
                  }
                  label="Push Notifications"
                />
              </FormControl>
            </Stack>
          </Stack>
        </Stack>
      }
    />
  );
};

export { Profile };
