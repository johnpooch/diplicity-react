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
import { useProfile } from "./use-profile";
import { QueryContainer } from "../../../components";
import { AppDispatch } from "../../../common";
import { useDispatch } from "react-redux";
import { authActions } from "../../../common/store/auth";
import { ScreenTopBar } from "../screen-title";

const Profile: React.FC = () => {
  const query = useProfile();

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
                      <MenuItem onClick={withMenuClose(onClickLogout)}>
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
