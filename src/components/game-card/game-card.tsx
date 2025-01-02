import React, { useState } from "react";
import {
  MoreHoriz,
  Share as ShareIcon,
  Info as InfoIcon,
  People as PeopleIcon,
  Lock as LockIcon,
  Add as JoinIcon,
  TimerOutlined as PhaseTimeRemainingIcon,
  Map as VariantIcon,
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
  Link,
} from "@mui/material";
import { useGameCard } from "./use-game-card";

const MAX_AVATARS = 7;
const AVATAR_SIZE = 28;

const GameCard: React.FC<{
  canJoin: boolean;
  canLeave: boolean;
  id: string;
  isPrivate: boolean;
  members: {
    id: string;
    src: string;
  }[];
  name: string;
  phase:
    | {
        season: string;
        year: number;
        type: string;
        timeRemaining?: string;
      }
    | undefined;
  phaseLength?: string;
  status: string;
  variant: string;
}> = (props) => {
  const theme = useTheme();
  const {
    onClickGameInfo,
    onClickPlayerInfo,
    onClickShare,
    onClickJoin,
    onClickLeave,
    onClickViewGame,
  } = useGameCard(props.id);

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

  const displayedUsers = props.members.slice(0, MAX_AVATARS);
  const remainingUsersCount = props.members.length - displayedUsers.length;

  return (
    <Card elevation={0}>
      <CardContent>
        <Stack>
          <Grid container spacing={2}>
            {/* Top */}
            <Grid container size={12} alignItems="center">
              <Grid size="grow">
                <Stack direction="row" alignItems="center" gap={1}>
                  {props.status !== "staging" ? (
                    <Link
                      href="#"
                      color="inherit"
                      underline="none"
                      onClick={onClickViewGame}
                    >
                      <Typography style={{ fontSize: "18px" }}>
                        {props.name}
                      </Typography>
                    </Link>
                  ) : (
                    <Typography variant="h4" style={{ fontSize: "18px" }}>
                      {props.name}
                    </Typography>
                  )}
                  {props.isPrivate && (
                    <LockIcon style={{ width: 16, height: 16 }} />
                  )}
                </Stack>
              </Grid>
              <Grid size="auto">
                <IconButton aria-label="menu" onClick={handleMenuClick}>
                  <MoreHoriz />
                </IconButton>
                <Menu anchorEl={anchorEl} open={open} onClose={handleMenuClose}>
                  <MenuItem onClick={withMenuClose(() => onClickGameInfo())}>
                    <InfoIcon sx={{ marginRight: 1 }} />
                    Game info
                  </MenuItem>
                  <MenuItem onClick={withMenuClose(() => onClickPlayerInfo())}>
                    <PeopleIcon sx={{ marginRight: 1 }} />
                    Player info
                  </MenuItem>
                  <Divider />
                  {props.canJoin && (
                    <MenuItem onClick={withMenuClose(() => onClickJoin())}>
                      <JoinIcon sx={{ marginRight: 1 }} />
                      Join
                    </MenuItem>
                  )}
                  {props.status === "started" && (
                    <MenuItem onClick={withMenuClose(() => onClickViewGame())}>
                      <VariantIcon sx={{ marginRight: 1 }} />
                      View
                    </MenuItem>
                  )}
                  {props.canLeave && (
                    <MenuItem onClick={withMenuClose(() => onClickLeave())}>
                      Leave
                    </MenuItem>
                  )}
                  <MenuItem onClick={withMenuClose(() => onClickShare())}>
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
                    {props.variant}
                  </Typography>
                  <Typography
                    variant="body2"
                    style={{
                      color: theme.palette.text.secondary,
                      fontSize: "15px",
                    }}
                  >
                    {props.phaseLength}
                  </Typography>
                </Stack>
              </Grid>
              <Grid
                container
                size="grow"
                justifyContent="flex-end"
                alignItems="center"
              >
                {props.phase && (
                  <>
                    <Typography
                      variant="body2"
                      style={{
                        color: theme.palette.text.secondary,
                        fontSize: "15px",
                      }}
                    >
                      {`${props.phase.season} ${props.phase.year}, ${props.phase.type}`}
                    </Typography>
                    {props.status === "started" && (
                      <Chip
                        icon={
                          <PhaseTimeRemainingIcon
                            style={{ width: 16, height: 16 }}
                          />
                        }
                        label={props.phase.timeRemaining}
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
                  onClick={() => onClickPlayerInfo()}
                  sx={{ cursor: "pointer" }}
                >
                  {displayedUsers.map((member) => (
                    <Avatar
                      sx={{
                        width: AVATAR_SIZE,
                        height: AVATAR_SIZE,
                      }}
                      key={member.id}
                      src={member.src}
                    />
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
                {props.canJoin && (
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={() => onClickJoin()}
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
