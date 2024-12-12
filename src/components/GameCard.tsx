import React, { useState } from "react";
import {
  Flag,
  MoreHoriz,
  Share as ShareIcon,
  Info as InfoIcon,
  People as PeopleIcon,
} from "@mui/icons-material";
import {
  Card,
  CardContent,
  Grid2 as Grid,
  IconButton,
  Typography,
  Menu,
  MenuItem,
  useTheme,
  Divider,
} from "@mui/material";
import PlayerAvatarStack from "./PlayerAvatarStack";
import StatusChip from "./StatusChip";

const GameCard: React.FC<{
  id: string;
  title: string;
  users: React.ComponentProps<typeof PlayerAvatarStack>["users"];
  onClickPlayerInfo: () => void;
  onClickGameInfo: () => void;
  onClickShare: () => void;
}> = ({ title, users, onClickPlayerInfo, onClickGameInfo, onClickShare }) => {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const handleMenuClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const withMenuClose = (callback: () => void) => () => {
    handleMenuClose();
    callback();
  };

  return (
    <Card>
      <CardContent>
        <Grid container spacing={2}>
          {/* Top */}
          <Grid container size={12} alignItems="center">
            <Grid size="auto">
              <Flag />
            </Grid>
            <Grid size="grow">
              <Typography variant="h4" style={{ fontSize: "18px" }}>
                {title}
              </Typography>
            </Grid>
            <Grid size="auto">
              <IconButton aria-label="menu" onClick={handleMenuClick}>
                <MoreHoriz />
              </IconButton>
              <Menu anchorEl={anchorEl} open={open} onClose={handleMenuClose}>
                <MenuItem onClick={withMenuClose(onClickGameInfo)}>
                  <InfoIcon sx={{ marginRight: 1 }} />
                  Game info
                </MenuItem>
                <MenuItem onClick={withMenuClose(onClickPlayerInfo)}>
                  <PeopleIcon sx={{ marginRight: 1 }} />
                  Player info
                </MenuItem>
                <Divider />
                <MenuItem onClick={withMenuClose(onClickShare)}>
                  <ShareIcon sx={{ marginRight: 1 }} />
                  Share
                </MenuItem>
              </Menu>
            </Grid>
          </Grid>
          {/* Middle */}
          <Grid container size={12}>
            <Grid size="grow" alignItems="center">
              <Grid>
                <Typography
                  variant="body2"
                  style={{
                    color: theme.palette.text.secondary,
                    fontSize: "15px",
                  }}
                >
                  Classical 2d
                </Typography>
              </Grid>
            </Grid>
            <Grid
              container
              size="grow"
              justifyContent="flex-end"
              alignItems="center"
            >
              <StatusChip status="confirmed" label="Orders confirmed" />
              <Typography variant="body2">{"<2d"}</Typography>
            </Grid>
          </Grid>
          {/* Bottom */}
          <Grid container size={12} alignItems="center">
            <Grid>
              <PlayerAvatarStack users={users} onClick={onClickPlayerInfo} />
            </Grid>
            <Grid container justifyContent="flex-end" size="grow">
              <Typography
                variant="body2"
                style={{
                  color: theme.palette.text.secondary,
                  fontSize: "15px",
                }}
              >
                Fall 1910, Adjustment
              </Typography>
            </Grid>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default GameCard;
