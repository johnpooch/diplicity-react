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
import { QueryContainer } from "../../components";
import {
  actions,
  AppDispatch,
  mergeQueries,
  service,
  useToggleMailEnabledMutation,
} from "../../common";
import { useDispatch } from "react-redux";
import { useMessaging } from "../../context";

const styles: Styles = {
  root: {
    gap: 2,
    alignItems: "center",
  },
};

const useProfile = () => {
  const dispatch = useDispatch<AppDispatch>();
  const getRootQuery = service.endpoints.getRoot.useQuery(undefined);
  const getUserConfigQuery = service.endpoints.getUserConfig.useQuery(
    getRootQuery.data?.Id || "",
    { skip: !getRootQuery.data }
  );
  const handleLogout = () => {
    dispatch(actions.logout());
  };

  const query = mergeQueries(
    [getRootQuery, getUserConfigQuery],
    (user, userConfig) => {
      return { ...user, ...userConfig };
    }
  );
  return { query, handleLogout };
};

const Profile: React.FC = () => {
  const { query, handleLogout } = useProfile();
  const { enabled, enableMessaging, disableMessaging } = useMessaging();
  const [toggleMailEnabled, toggleMailEnabledMutation] =
    useToggleMailEnabledMutation();
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
    <QueryContainer query={query}>
      {(data) => (
        <Stack>
          <Grid2 container sx={styles.root} p={2}>
            <Grid2 size="auto">
              <Avatar src={data.Picture} alt={data.Name} />
            </Grid2>
            <Grid2 size="grow">
              <Typography variant="body1">{data.Name}</Typography>
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
                      onChange={() => {
                        if (!enabled) {
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
              <FormControl>
                <FormControlLabel
                  control={
                    <Switch
                      checked={data.MailConfig?.Enabled ?? false}
                      disabled={toggleMailEnabledMutation.isLoading}
                      onChange={() => {
                        toggleMailEnabled(!data.MailConfig?.Enabled);
                      }}
                      name="mail"
                    />
                  }
                  label="Email Notifications"
                />
              </FormControl>
            </Stack>
          </Stack>
        </Stack>
      )}
    </QueryContainer>
  );
};

export { Profile };
