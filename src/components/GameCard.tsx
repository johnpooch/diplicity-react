import React, { useState } from "react";
import {
  Flag,
  MoreHoriz,
  Share as ShareIcon,
  Info as InfoIcon,
  People as PeopleIcon,
  Lock as LockIcon,
  Add as JoinIcon,
  TimerOutlined as PhaseTimeRemainingIcon,
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
  Stack,
  Button,
  Chip,
} from "@mui/material";
import PlayerAvatarStack from "./PlayerAvatarStack";
import StatusChip from "./StatusChip";

const orderStatusLabelMap: Record<
  React.ComponentProps<typeof StatusChip>["status"],
  string
> = {
  missed: "Orders missed",
  unconfirmed: "Orders not confirmed",
  pending: "Orders pending",
  confirmed: "Orders confirmed",
};

const GameCard: React.FC<{
  id: string;
  title: string;
  users: React.ComponentProps<typeof PlayerAvatarStack>["users"];
  onClickPlayerInfo: () => void;
  onClickGameInfo: () => void;
  onClickShare: () => void;
  onClickJoin: () => void;
  onClickLeave: () => void;
  status: "staging" | "active" | "finished";
  private: boolean;
  canJoin: boolean;
  canLeave: boolean;
  variant: string;
  phaseDuration: string;
  timeLeft?: string;
  ordersStatus?: React.ComponentProps<typeof StatusChip>["status"];
  link: string;
}> = ({
  title,
  users,
  onClickPlayerInfo,
  onClickGameInfo,
  onClickShare,
  onClickJoin,
  onClickLeave,
  private: isPrivate,
  canJoin,
  canLeave,
  variant,
  phaseDuration,
  timeLeft,
  ordersStatus,
}) => {
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
    <Card elevation={0}>
      <CardContent>
        <Stack>
          <Grid container spacing={2}>
            {/* Top */}
            <Grid container size={12} alignItems="center">
              <Grid size="auto">
                <Flag />
              </Grid>
              <Grid size="grow">
                <Stack direction="row" alignItems="center" gap={1}>
                  <Typography variant="h4" style={{ fontSize: "18px" }}>
                    {title}
                  </Typography>
                  {isPrivate && <LockIcon style={{ width: 16, height: 16 }} />}
                  {ordersStatus && (
                    <StatusChip
                      status={ordersStatus}
                      label={orderStatusLabelMap[ordersStatus]}
                    />
                  )}
                </Stack>
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
                  {canJoin && (
                    <MenuItem onClick={withMenuClose(onClickJoin)}>
                      <JoinIcon sx={{ marginRight: 1 }} />
                      Join
                    </MenuItem>
                  )}
                  {canLeave && (
                    <MenuItem onClick={withMenuClose(onClickLeave)}>
                      Leave
                    </MenuItem>
                  )}
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
                <Stack direction="row" gap={1}>
                  <Typography
                    variant="body2"
                    style={{
                      color: theme.palette.text.secondary,
                      fontSize: "15px",
                    }}
                  >
                    {variant}
                  </Typography>
                  <Typography
                    variant="body2"
                    style={{
                      color: theme.palette.text.secondary,
                      fontSize: "15px",
                    }}
                  >
                    {phaseDuration}
                  </Typography>
                </Stack>
              </Grid>
              <Grid
                container
                size="grow"
                justifyContent="flex-end"
                alignItems="center"
              >
                <Typography
                  variant="body2"
                  style={{
                    color: theme.palette.text.secondary,
                    fontSize: "15px",
                  }}
                >
                  Fall 1910, Adjustment
                </Typography>
                {timeLeft && (
                  <Chip
                    icon={
                      <PhaseTimeRemainingIcon
                        style={{ width: 16, height: 16 }}
                      />
                    }
                    label={timeLeft}
                  />
                )}
              </Grid>
            </Grid>
            {/* Bottom */}
            <Grid container size={12} alignItems="center">
              <Grid>
                <PlayerAvatarStack users={users} onClick={onClickPlayerInfo} />
              </Grid>
              <Grid container justifyContent="flex-end" size="grow">
                {canJoin && (
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={onClickJoin}
                    size="small"
                  >
                    Join
                  </Button>
                )}
              </Grid>
            </Grid>
          </Grid>
        </Stack>
      </CardContent>
    </Card>
  );
};

export default GameCard;
