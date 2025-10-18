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
  Alert,
  TextField,
} from "@mui/material";
import { HomeLayout } from "./Layout";
import { authSlice, service } from "../../store";
import { NotificationBanner } from "../../components/NotificationBanner";
import { HomeAppBar } from "./AppBar";
import { IconName } from "../../components/Icon";
import { IconButton } from "../../components/Button";
import { useMessaging } from "../../context";
import { useDispatch } from "react-redux";
import { useNavigate } from "react-router";

const Profile: React.FC = () => {
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const query = service.endpoints.userRetrieve.useQuery();
  const [updateProfile, updateProfileMutation] =
    service.endpoints.userUpdatePartialUpdate.useMutation();
  const {
    enableMessaging,
    enabled,
    disableMessaging,
    permissionDenied,
    error,
  } = useMessaging();

  const [isEditingName, setIsEditingName] = useState(false);
  const [editedName, setEditedName] = useState("");

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

  const handleStartEditName = () => {
    setEditedName(query.data?.name || "");
    setIsEditingName(true);
  };

  const handleCancelEditName = () => {
    setIsEditingName(false);
    setEditedName("");
  };

  const handleSaveName = async () => {
    if (editedName.trim().length >= 2) {
      try {
        await updateProfile({
          patchedUserProfileUpdate: { name: editedName.trim() },
        }).unwrap();
        setIsEditingName(false);
        setEditedName("");
      } catch (err) {
        // Error will be shown via updateProfileMutation.error
      }
    }
  };

  if (query.isError) {
    return <div>Error</div>;
  }

  return (
    <HomeLayout
      appBar={
        <HomeAppBar title="Profile" onNavigateBack={() => navigate("/")} />
      }
      content={
        <Stack>
          <NotificationBanner />
          <Grid2 container p={2} alignItems="center" gap={2}>
            <Grid2 size="auto">
              {query.isLoading ? (
                <Skeleton variant="circular" width={40} height={40} />
              ) : (
                <Avatar src={query.data?.picture} alt={query.data?.name} />
              )}
            </Grid2>
            <Grid2 size="grow">
              {query.isLoading ? (
                <Skeleton variant="text" width={150} height={24} />
              ) : isEditingName ? (
                <Stack direction="row" alignItems="center" gap={1}>
                  <TextField
                    value={editedName}
                    onChange={e => setEditedName(e.target.value)}
                    autoFocus
                    size="small"
                    disabled={updateProfileMutation.isLoading}
                    error={updateProfileMutation.isError}
                    helperText={
                      updateProfileMutation.isError
                        ? "Failed to update name. Please try again."
                        : ""
                    }
                    onKeyDown={e => {
                      if (e.key === "Enter") {
                        handleSaveName();
                      } else if (e.key === "Escape") {
                        handleCancelEditName();
                      }
                    }}
                  />
                  <IconButton
                    aria-label="save"
                    onClick={handleSaveName}
                    icon={IconName.Success}
                    disabled={
                      updateProfileMutation.isLoading ||
                      editedName.trim().length < 2
                    }
                  />
                  <IconButton
                    aria-label="cancel"
                    onClick={handleCancelEditName}
                    icon={IconName.Close}
                    disabled={updateProfileMutation.isLoading}
                  />
                </Stack>
              ) : (
                <Stack direction="row" alignItems="center" gap={1}>
                  <Typography variant="body1">{query.data?.name}</Typography>
                  <IconButton
                    aria-label="edit name"
                    onClick={handleStartEditName}
                    icon={IconName.Edit}
                  />
                </Stack>
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
            <Stack gap={2}>
              {error && <Alert severity="error">{error}</Alert>}
              {permissionDenied && !error && (
                <Alert severity="warning">
                  Notifications are blocked in your browser. To enable them,
                  click the icon in your address bar and allow notifications.
                </Alert>
              )}
              <FormControl>
                <FormControlLabel
                  control={
                    <Switch
                      checked={enabled}
                      disabled={permissionDenied}
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
