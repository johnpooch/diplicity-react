import React, { useState } from "react";
import {
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
  Avatar,
} from "@mui/material";
import StatusChip from "./StatusChip";
import { Display } from "../common/display";
import PlayerAvatar from "./PlayerAvatar";
import { useGlobalModal } from "../GlobalModalContext";

const MAX_AVATARS = 7;

const orderStatusLabelMap: Record<
  React.ComponentProps<typeof StatusChip>["status"],
  string
> = {
  missed: "Orders missed",
  unconfirmed: "Orders not confirmed",
  pending: "Orders pending",
  confirmed: "Orders confirmed",
};

type GameCallback = (id: string) => void;

type GameCallbacks = {
  onClickPlayerInfo: GameCallback;
  onClickGameInfo: GameCallback;
  onClickShare: GameCallback;
  onClickJoin: GameCallback;
  onClickLeave: GameCallback;
};

const GameCard: React.FC<Display.Game & GameCallbacks> = (props) => {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);

  const { openModal } = useGlobalModal();

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

  const displayedUsers = props.users.slice(0, MAX_AVATARS);
  const remainingUsersCount = props.users.length - displayedUsers.length;

  return (
    <Card elevation={0}>
      <CardContent>
        <Stack>
          <Grid container spacing={2}>
            {/* Top */}
            <Grid container size={12} alignItems="center">
              {props.user && props.user.nation && (
                <Grid size="auto">
                  <Avatar
                    style={{ width: 24, height: 24 }}
                    src={`https://diplicity-engine.appspot.com/Variant/${props.variant.name}/Flags/${props.user?.nation}.svg`}
                  />
                </Grid>
              )}
              <Grid size="grow">
                <Stack direction="row" alignItems="center" gap={1}>
                  <Typography variant="h4" style={{ fontSize: "18px" }}>
                    {props.title}
                  </Typography>
                  {props.private && (
                    <LockIcon style={{ width: 16, height: 16 }} />
                  )}
                  <StatusChip
                    status={"confirmed"}
                    label={orderStatusLabelMap["confirmed"]}
                  />
                </Stack>
              </Grid>
              <Grid size="auto">
                <IconButton aria-label="menu" onClick={handleMenuClick}>
                  <MoreHoriz />
                </IconButton>
                <Menu anchorEl={anchorEl} open={open} onClose={handleMenuClose}>
                  <MenuItem
                    onClick={withMenuClose(() =>
                      openModal("gameInfo", props.id)
                    )}
                  >
                    <InfoIcon sx={{ marginRight: 1 }} />
                    Game info
                  </MenuItem>
                  <MenuItem
                    onClick={withMenuClose(() =>
                      openModal("playerInfo", props.id)
                    )}
                  >
                    <PeopleIcon sx={{ marginRight: 1 }} />
                    Player info
                  </MenuItem>
                  <Divider />
                  {props.userCanJoin && (
                    <MenuItem
                      onClick={withMenuClose(() => props.onClickJoin(props.id))}
                    >
                      <JoinIcon sx={{ marginRight: 1 }} />
                      Join
                    </MenuItem>
                  )}
                  {props.userCanLeave && (
                    <MenuItem
                      onClick={withMenuClose(() =>
                        props.onClickLeave(props.id)
                      )}
                    >
                      Leave
                    </MenuItem>
                  )}
                  <MenuItem
                    onClick={withMenuClose(() => props.onClickShare(props.id))}
                  >
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
                    {props.variant.name}
                  </Typography>
                  <Typography
                    variant="body2"
                    style={{
                      color: theme.palette.text.secondary,
                      fontSize: "15px",
                    }}
                  >
                    {props.movementPhaseDuration}
                  </Typography>
                </Stack>
              </Grid>
              <Grid
                container
                size="grow"
                justifyContent="flex-end"
                alignItems="center"
              >
                {props.currentPhase && (
                  <>
                    <Typography
                      variant="body2"
                      style={{
                        color: theme.palette.text.secondary,
                        fontSize: "15px",
                      }}
                    >
                      {`${props.currentPhase.season} ${props.currentPhase.year}, ${props.currentPhase.type}`}
                    </Typography>
                    {props.status === "started" && (
                      <Chip
                        icon={
                          <PhaseTimeRemainingIcon
                            style={{ width: 16, height: 16 }}
                          />
                        }
                        label={props.currentPhase.remaining}
                      />
                    )}
                  </>
                )}
              </Grid>
            </Grid>
            {/* Bottom */}
            <Grid container size={12} alignItems="center">
              <Grid>
                <Stack
                  direction="row"
                  spacing={-1}
                  alignItems="center"
                  onClick={() => props.onClickPlayerInfo(props.id)}
                  sx={{ cursor: "pointer" }}
                >
                  {displayedUsers.map((user, index) => (
                    <PlayerAvatar key={index} username={user.username} />
                  ))}
                  {remainingUsersCount > 0 && (
                    <Typography
                      variant="body2"
                      sx={{ paddingLeft: 1, alignSelf: "center" }}
                    >
                      +{remainingUsersCount}
                    </Typography>
                  )}
                </Stack>
              </Grid>
              <Grid container justifyContent="flex-end" size="grow">
                {props.userCanJoin && (
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => props.onClickJoin(props.id)}
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

export { GameCard };
export type { GameCallbacks };
