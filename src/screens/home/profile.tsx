import React, { useState } from "react";
import {
  Avatar,
  Divider,
  FormControl,
  FormControlLabel,
  Grid2,
  IconButton,
  Menu,
  MenuItem,
  Stack,
  Switch,
  Typography,
} from "@mui/material";
import { MoreHoriz } from "@mui/icons-material";
import { useDispatch } from "react-redux";
import { authSlice, service } from "../../store";
import { useMessaging } from "../../context";
import { QueryContainer } from "../../components";

const Profile: React.FC = () => {
  const dispatch = useDispatch();
  const userProfileQuery = service.endpoints.userRetrieve.useQuery();
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

  return (
    <QueryContainer query={userProfileQuery}>
      {(user) => (
        <Stack>
          <Grid2 container sx={styles.root} p={2}>
            <Grid2 size="auto">
              <Avatar src={user.picture} alt={user.username} />
            </Grid2>
            <Grid2 size="grow">
              <Typography variant="body1">{user.username}</Typography>
            </Grid2>
            <Grid2 size="auto">
              <IconButton aria-label="menu" onClick={handleMenuClick}>
                <MoreHoriz />
              </IconButton>
              <Menu anchorEl={anchorEl} open={open} onClose={handleMenuClose}>
                <MenuItem onClick={withMenuClose(handleLogout)}>
                  Logout
                </MenuItem>
              </Menu>
            </Grid2>
          </Grid2>
          <Divider />
          <Stack p={2} gap={2}>
            <Typography variant="h4" sx={{ margin: 0 }}>
              Notifications
            </Typography>
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
      )}
    </QueryContainer>
  );
};

const styles: Styles = {
  root: {
    gap: 2,
    alignItems: "center",
  },
};

export { Profile };
